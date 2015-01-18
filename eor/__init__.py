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

    from .utils.config import parse_app_settings
    # 'qooxdoo-app-version': dict(convert=unicode, variants=['source', 'build'], default='build')
    parse_app_settings(settings, {
        'debug-auth':            dict(convert=asbool, default=False),
        'static-serial':         dict(convert=unicode, default=''),
        'store-path':            dict(convert=unicode),

        'less':                  dict(convert=unicode, default='static'),
        'lessc-path':            dict(convert=unicode),

        'email-from':            dict(convert=unicode),
        'smtp-host':             dict(convert=unicode, default='localhost'),

        'main-domain':           dict(convert=unicode),
        'main-domain-base':      dict(convert=unicode),

        'twitter-api-key':       dict(convert=unicode),
        'twitter-api-secret':    dict(convert=unicode),

        'facebook-app-id':       dict(convert=unicode),
        'facebook-app-secret':   dict(convert=unicode),

        'vkontakte-app-id':      dict(convert=unicode),
        'vkontakte-app-secret':  dict(convert=unicode)
    })

    ## sessions

    from pyramid_beaker import session_factory_from_settings
    config.set_session_factory(session_factory_from_settings(settings))

    ## renderers

    config.include('pyramid_mako')

    ## utils

    config.include('.utils')
    config.include('.error')
    config.include('.models')
    config.include('.render')
    config.include('.asset_utils')
    config.include('.auth')
    config.include('.captcha')
    # TODO rest

    ## scan

    #config.scan() TODO

    ## done

    log.info("app server initialized")


"""
    run from pserve
    
from tfadmin.models import initialize_sqlalchemy
initialize_sqlalchemy({'sqlalchemy.url': 'postgresql+psycopg2://tf:tf@localhost/tf'})
from sqlalchemy.orm import compile_mappers ; compile_mappers()
from tfadmin.models import Session
from tfadmin.models.contracts import Client, Contract
"""
