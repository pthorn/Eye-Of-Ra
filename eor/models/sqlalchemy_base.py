# coding: utf-8

import logging
log = logging.getLogger(__name__)


import sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension

from ..config import config


class BaseMixin(object):

    @classmethod
    def get_count(cls):
        return Session().query(cls).count()

    def add(self, flush=False):
        Session().add(self)
        if flush:
            Session().flush()

    def delete(self, flush=False):
        Session().delete(self)
        if flush:
            Session().flush()

    def expunge(self):
        Session().expunge(self)


def get_declarative_base():
    superclasses = config.sqlalchemy_base_superclasses

    if not superclasses:
        superclasses = ()
    elif not isinstance(superclasses, tuple):
        superclasses = (superclasses,)

    superclasses += (BaseMixin,)
    log.debug('sqlalchemy base superclasses: %s', superclasses)

    # http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/mixins.html#augmenting-the-base
    # http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/api.html#sqlalchemy.ext.declarative.declarative_base
    return declarative_base(cls=superclasses)


Base = get_declarative_base()
Session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def initialize_sqlalchemy(settings):

    def pgsql_version():
        return Session().connection().execute("select version()").fetchone()[0]

    def psycopg2_version():
        import psycopg2
        return psycopg2.__version__

    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    Base.metadata.bind = engine

    log.info('sqlalchemy version %s configured with url %s' % (sqlalchemy.__version__, settings['sqlalchemy.url'])) # TODO prints password into log!
    log.info('driver: psycopg2 %s' % psycopg2_version())
    log.info('connected to database: %s' % pgsql_version())
