# coding: utf-8

import logging
log = logging.getLogger(__name__)

from sqlalchemy import Column, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import and_, or_, not_, text
from sqlalchemy.sql.expression import func, case

from zope.sqlalchemy import ZopeTransactionExtension


Base = declarative_base()
Session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def initialize_sqlalchemy(settings):

    def pgsql_version():
        return Session().connection().execute("select version()").fetchone()[0]

    def psycopg2_version():
        import psycopg2
        return psycopg2.__version__

    from sqlalchemy import engine_from_config
    import sqlalchemy
    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    Base.metadata.bind = engine
    log.info('sqlalchemy version %s configured with url %s' % (sqlalchemy.__version__, settings['sqlalchemy.url'])) # TODO prints password into log!
    log.info('driver: psycopg2 %s' % psycopg2_version())
    log.info('connected to database: %s' % pgsql_version())


class BaseMixin(object):

    @classmethod
    def get_by_id(cls, id):
        return Session.query(cls)\
            .filter(cls.id == id)\
            .one()

    @classmethod
    def get_for_rest_grid(cls, start=0, limit=None, order=None, search=None, filters=None, query=None):
        """
        cls._rest_search_columns = [cls.name, cls.description] - list of columns for search filtering
        :param start: number (default 0)
        :param limit: number or None
        :param order: {col: '', dir: 'asc|desc'} or None
        :param search:
        :param filters:
        :param query: sqlalchemy query
        :return: result of an executed query
        """

        def apply_filters(query):
            for key, val in filters.iteritems():
                op, field_name = key.split('_', 1)

                try:
                    field = getattr(cls, field_name)
                except AttributeError:
                    log.error(u'get_for_rest_grid: filter "%s=%s": unknown attribute %s' % (key, val, field_name))
                    continue

                if op == 'e':
                    query = query.filter(field == val)
                elif op == 'n':
                    query = query.filter(or_(field == val, field == None))
                elif op == 'l':
                    query = query.filter(func.lower(field).like('%' + val.lower() + '%'))
                elif op == 's':
                    query = query.filter(func.lower(field).like(val.lower() + '%'))
                else:
                    log.error(u'get_for_rest_grid: filter "%s=%s": unknown op: %s' % (key, val, op))

            return query

        def apply_order(query):
            from sqlalchemy.orm.relationships import RelationshipProperty
            from sqlalchemy.orm.properties import  ColumnProperty

            order_split = order['col'].split('.')

            try:
                order_attr = getattr(cls, order_split[0])
            except AttributeError:
                log.error(u'get_for_rest_grid: sort key %s: unknown attribute %s.%s' % (order['col'], cls.__name__, order['col']))
                return query

            for el in order_split[1:]:
                if not isinstance(order_attr.property, RelationshipProperty):
                    log.error(u'get_for_rest_grid: sort key %s: not a RelationshipProperty: %s' % (order['col'], str(order_attr.property)))
                    return query

                entity = order_attr.property.mapper.entity

                try:
                    order_attr = getattr(entity, el)
                except AttributeError:
                    log.error(u'get_for_rest_grid: sort key %s: unknown attribute %s.%s' % (order['col'], entity.__name__, el))
                    return query

            if not isinstance(order_attr.property, ColumnProperty):
                log.error(u'get_for_rest_grid: sort key %s: not a ColumnProperty: %s' % (order['col'], str(order_attr.property)))
                return query

            return query.order_by(desc(order_attr) if order['dir'] == 'desc' else order_attr)

        if not query:
            query = Session.query(cls)

        search_columns = getattr(cls, '_rest_search_columns', [])
        if search and len(search_columns) > 0 and search.strip():
            search = search.strip().lower()
            if len(search_columns) == 1:
                col = search_columns[0]
                search_filter = func.lower(col).like('%' + search + '%')
            else:  # > 1
                clauses = [func.lower(col).like('%' + search + '%') for col in search_columns]
                search_filter = or_(*clauses)
            query = query.filter(search_filter)

        if filters:
            query = apply_filters(query)

        if order:
            query = apply_order(query)

        count = query.count()
        result = query[start:start+limit] if limit else query[start:]

        return count, result

    @classmethod
    def get_count(cls):
        return Session.query(cls).count()

    def add(self, flush=False):
        Session.add(self)
        if flush:
            Session.flush()

    def delete(self):
        Session.delete(self)

    def expunge(self):
        Session.expunge(self)
