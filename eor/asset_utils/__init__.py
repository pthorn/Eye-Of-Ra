# coding: utf-8

from .webpack import webpack_asset


def includeme(config):
    settings = config.get_settings()

    from eor_settings import ParseSettings

    (ParseSettings(settings, prefix='eor')
        .path('webpack-asset-path', default='../static/gen')
        .string('webpack-asset-defs', default='webpack-assets.json')
        .string('webpack-asset-url-prefix')
        .bool('webpack-asset-autoreload', default=False))

    from .webpack import load_definitions
    load_definitions()
