# coding: utf-8

import logging
log = logging.getLogger(__name__)

from pyramid.config import Configurator
from pyramid.settings import asbool

from .utils import app_conf


def includeme(config):
    settings = config.get_settings()

    log.info("initializing app server")

    ## settings

    from .utils.settings import ParseSettings

    (ParseSettings(settings, prefix='eor.')
        .string('mode', default='dev', variants=('dev', 'prod'))
        .string('domain')  # TODO in asset_utils?
        .string('static-domain')
        .string('static-serial', default=''))

    ## sessions

    from pyramid_beaker import session_factory_from_settings
    config.set_session_factory(session_factory_from_settings(settings))

    ## renderers

    config.include('pyramid_mako')

    ## utils

    config.include('.utils')
    config.include('.error')
    config.include('.models')  # initialize sqlalchemy, connect to database
    config.include('.render')
    config.include('.asset_utils')
    config.include('.auth')

    ## done

    log.info("app server initialized")
