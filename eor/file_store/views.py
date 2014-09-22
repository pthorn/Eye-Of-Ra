#coding: utf-8

import logging
log = logging.getLogger(__name__)

import os
import errno

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
import transaction

from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPBadRequest
from pyramid.view import view_config

from .. import models
from ..utils import app_conf
from .image import save_uploaded_image, get_image_format, NotAnImageException
from .config import Original, Thumbnail
from ..rest.rest import entities_as_list, rest_list


class ImageViews(object):
    """
    """

    entity         = None
    file_req_param = 'file'
    #thumbnails     = []

    def __init__(self, request):
        self.request = request
        self.c = request.tmpl_context

    def create_entity(self):
        """
        Override this method to set additional properties on the object
        :return: entity object
        """
        return self.entity()

    # def list_view(self):
    #     """
    #     List view, GET
    #     :return: response (renderer='json')
    #     """
    #     def list_to_json(l):
    #         return entities_as_list(l, ['id', 'ext'])
    #     return rest_list(self.request, self.entity, list_to_json)

    def upload_view(self):
        """
        Upload view, POST
        :return: response (renderer='json')
        """
        try:
            file_obj = self.request.params[self.file_req_param]
        except KeyError as e:
            log.warn('bad request parameters: %s' % e)
            raise HTTPBadRequest()

        self.obj = self.create_entity()
        self.obj.ext = get_image_format(file_obj)
        self.obj.add(flush=True)  # to get the id

        try:
            save_uploaded_image(file_obj, self.obj)
        except NotAnImageException:
            transaction.doom()
            return {'status': 'error', 'code': 'not-an-image'}
        except Exception, e:
            transaction.doom()
            log.exception(u'exception when saving image')
            return {'status': 'error'}

        return {'status': 'ok', 'id': self.obj.id}

    #@view_config(route_name='admin-rest-offerphoto-delete', renderer='json', permission='access')
    # view
    def delete_view(self):
        image_id = self.request.matchdict['id']
        try:
            image = self.entity.get_by_id(image_id)
        except NoResultFound:
            return {'status': 'error', 'code': 'object-not-found'}

        for key in self.entity.variants.keys():
            try:
                os.unlink(image.get_path(key))
            except OSError as e:
                if e.errno == errno.ENOENT:
                    pass
                else:
                    raise

        try:
            image.delete()
            return {'status': 'ok'}
        except SQLAlchemyError as e:
            return {'status': 'error', 'message': u'Ошибка базы данных при удалении\n' + unicode(e).replace(u"' {'", u"'\n{'")}
