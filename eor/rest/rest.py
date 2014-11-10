# coding: utf-8

import datetime

import logging
log = logging.getLogger(__name__)

import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

import colander

from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from .. import models
from ..utils import app_conf
from ..auth import ebff


class _do_not_set(object): pass
do_not_set = _do_not_set()  # marker object for admin-only properties so they're not altered by normal users TODO check permissions!


def add_rest_routes(adder, entity, url_prefix='/wsd/rest', name_prefix='wsd-rest', suffix=''):
    adder(name_prefix + '-%s-list%s' % (entity, suffix),      R'%s/%s' % (url_prefix, entity),       request_method='GET',    factory=ebff('admin-panel'))
    adder(name_prefix + '-%s-create%s' % (entity, suffix),    R'%s/%s' % (url_prefix, entity),       request_method='POST',   factory=ebff('admin-panel'))
    adder(name_prefix + '-%s-get-by-id%s' % (entity, suffix), R'%s/%s/{id}' % (url_prefix, entity),  request_method='GET',    factory=ebff('admin-panel'))
    adder(name_prefix + '-%s-update%s' % (entity, suffix),    R'%s/%s/{id}' % (url_prefix, entity),  request_method='PUT',    factory=ebff('admin-panel'))
    adder(name_prefix + '-%s-delete%s' % (entity, suffix),    R'%s/%s/{id}' % (url_prefix, entity),  request_method='DELETE', factory=ebff('admin-panel'))


def rest_get_by_id(request, entity, getter=None, getter_args=None, additional=None):
    if not getter:
        getter = getattr(entity, 'get_by_id_rest', entity.get_by_id)

    if not getter_args:
        getter_args = [request.matchdict['id']]

    try:
        obj = getter(*getter_args)
    except NoResultFound:
        return {'status': 'error', 'message': u'Объекта не существует.'}

    return {'status': 'ok', 'data': entity_as_dict(obj, additional=additional)}


def rest_list(request, entity, list_to_json, get_args=None):
    """
    A skeleton for a REST list handler.
    :param request: pyramid request
    :param entity: SQLALchemy entity
    :param list_to_json: function to convert list of entities into a list for json
    :return: JSON response
    """

    try:
        start = int(request.params['s'])
    except (KeyError, ValueError):
        start = 0
    try:
        limit = int(request.params['l'])
    except (KeyError, ValueError):
        limit = None

    order_s = request.params.get('o', None)
    if order_s:
        order = {'col': order_s.lstrip('-'),'dir': 'desc' if order_s.startswith(u'-') else 'asc'}
    else:
        order = None

    search = request.params.get('q', None)

    filters = dict()
    for param, val in request.params.iteritems():
        if param.startswith('f'):
            filters[param[1:]] = val

    if not get_args:
        get_args = dict()

    try:
        count, objs = entity.get_for_rest_grid(start, limit, order=order, search=search, filters=filters or None, **get_args)
    except SQLAlchemyError, e:
        return {'status': 'error', 'message': unicode(e)}

    return {
        'status': 'ok',
        'count': count,
        'data': list_to_json(objs)
    }


def rest_create(request, entity, schema,
                after_create_obj=None,
                create_func=None,
                after_create_func=None,
                before_update_obj=None,
                id_field='id',
                cstruct=None):

    if not cstruct:
        cstruct = request.json_body  # TODO exception!!

    try:
        deserialized = schema.deserialize(cstruct)
    except colander.Invalid, e:
        return {'status': 'invalid', 'errors': e.asdict()}

    obj = entity()

    if before_update_obj:
        before_update_obj(obj, deserialized)

    update_entity_from_appstruct(obj, deserialized)

    if after_create_obj:
        after_create_obj(obj, deserialized)

    if create_func:
        create_func(obj)
    else:
        try:
            obj.add(flush=True)
        except SQLAlchemyError, e:
            exc_message = str(e).decode('utf-8', errors='replace').replace(u"' {'", u"'\n{'")
            log.warn(u'exception: %s' % exc_message)
            #log_access(request, 'EXCEPTION save %s id=%s %s' % (obj.__class__.__name__, obj.id, unicode(exc))) TODO
            return {'status': 'error', 'message': u'Ошибка базы данных при сохранении\n' + exc_message}

    if after_create_func:
        after_create_func(obj, deserialized)

    return {'status': 'ok', 'id': getattr(obj, id_field)}


def rest_update(request, entity, schema, getter=None, getter_args=None, before_update_obj=None, after_update_obj=None):
    try:
        deserialized = schema.deserialize(request.json_body)
    except colander.Invalid, e:
        return {'status': 'invalid', 'errors': e.asdict()}

    if not getter:
        getter = entity.get_by_id

    if not getter_args:
        getter_args = [request.matchdict['id']]

    try:
        obj = getter(*getter_args)
    except NoResultFound:
        return {'status': 'error', 'message': u'Объекта не существует, id=%s' % getter_args}

    if before_update_obj:
        before_update_obj(obj, deserialized)

    update_entity_from_appstruct(obj, deserialized)

    if after_update_obj:
        after_update_obj(obj, deserialized)

    try:
        obj.add(flush=True)
    except SQLAlchemyError, e:
        #log_access(request, 'EXCEPTION save %s id=%s %s' % (obj.__class__.__name__, obj.id, unicode(exc))) TODO
        return {'status': 'error', 'message': u'Ошибка базы данных при сохранении\n' + unicode(e).replace(u"' {'", u"'\n{'")} # TODO e

    return {'status': 'ok', 'id': obj.id}


def rest_delete(request, entity):
    # TODO
    pass


def entity_as_dict(entity, include=None, additional=None, remove=None):
    # TODO exclude some attributes if admin_mode=False?
    # see http://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript
    # isinstance(p, sqlalchemy.orm.properties.ColumnProperty) isinstance(p, sqlalchemy.orm.properties.RelationshipProperty)

    mapper = inspect(entity.__class__)

    if not include:
        include = [p.key for p in mapper.iterate_properties if isinstance(p, sqlalchemy.orm.properties.ColumnProperty)]

    if additional:
        include.extend(additional)

    if remove:
        remove = frozenset(remove)
        include = [el for el in include if el not in remove]

    include = [key.split('.') if key.find('.') != -1 else key for key in include]

    res = dict()
    for key in include:
        if isinstance(key, basestring):
            res[key] = getattr(entity, key)
        else:
            p = entity
            r = res
            for el in key[:-1]:
                p = getattr(p, el)
                if el not in r:
                    r[el] = dict()
                r = r[el]
            r[key[-1]] = getattr(p, key[-1])

    return res


def entities_as_list(lst, include=None, additional=None, remove=None):
    return[entity_as_dict(e, include, additional, remove) for e in lst]


def update_entity_from_appstruct(entity, appstruct):
    for key, val in appstruct.iteritems():
        if val is not do_not_set:
            setattr(entity, key, val)


########################################################################################################################


class MyDate(object):

    def __init__(self, format=u"%d.%m.%Y"):
        self.format = format

    def serialize(self, node, appstruct):
        if not appstruct:
            return colander.null # TODO what does colander.null mean during serialization?

        if isinstance(appstruct, datetime.datetime):
            appstruct = appstruct.date()

        if not isinstance(appstruct, datetime.date):
            raise colander.Invalid(node, 'not a date object')

        return appstruct.strftime(self.format)

    def deserialize(self, node, cstruct):
        if not cstruct:
            return colander.null

        try:
            return datetime.datetime.strptime(cstruct, self.format).date()
        except ValueError:
            raise colander.Invalid(node, u"Неправильный формат даты")


class MyDateTime(object):

    def __init__(self, format=u"%d.%m.%Y %H:%M:%S"):
        self.format = format

    def serialize(self, node, appstruct):
        if not appstruct:
            return colander.null # TODO what does colander.null mean during serialization?

        if not isinstance(appstruct, datetime.datetime):
            raise colander.Invalid(node, 'not a datetime object')

        return appstruct.strftime(self.format)

    def deserialize(self, node, cstruct):
        if not cstruct:
            return colander.null

        try:
            return datetime.datetime.strptime(cstruct, self.format)
        except ValueError:
            raise colander.Invalid(node, u"Неправильный формат даты/времени")


class MyFile(object):

    def __init__(self):
        pass

    def serialize(self, node, appstruct):
        return None # serializing doesn't make any sense

    def deserialize(self, node, cstruct):
        # cgi.FieldStorage seems to be always false. however, when user
        # doesn't select a file cstructs seems to be u'' so test for that
        if cstruct is colander.null or (isinstance(cstruct, basestring) and not cstruct):
            return colander.null
        import cgi
        if not isinstance(cstruct, cgi.FieldStorage):
            raise colander.Invalid(node, u"expected FieldStorage (how about some enctype?)")
        return cstruct
