# coding: utf-8

"""
{
    'admin': {'js': 'admin.bundle.c875011f3872b3b6b154.js'},
    'libs': {'js': 'libs.bundle.c875011f3872b3b6b154.js'},
    'site': {'js': 'site.bundle.c875011f3872b3b6b154.js'}
}

"""

import logging
log = logging.getLogger(__name__)

import os
import json

from ..utils import app_conf


_definitions = {}
_last_modified = None


def load_definitions():
    defs_path = os.path.join(app_conf('eor.webpack-asset-path'), app_conf('eor.webpack-asset-defs'))

    try:
        last_modified = os.path.getmtime(defs_path)
    except OSError as e:
        log.error('eor.asset_utils: error loading %s: %s (eor.webpack-asset-path = %s, eor.webpack-asset-defs = %s)',
          defs_path, e, app_conf('eor.webpack-asset-path'), app_conf('eor.webpack-asset-defs'))
        return

    if last_modified == _last_modified:
        return

    global _last_modified
    _last_modified = last_modified

    with open(defs_path, 'r') as f:
        s = f.read()

    global _definitions
    _definitions = json.loads(s)


def webpack_asset(bundle, kind='js', add_serial=False):
    if app_conf('eor.webpack-asset-autoreload'):
        load_definitions()

    res = app_conf('eor.webpack-asset-url-prefix') + _definitions[bundle][kind]
    if add_serial:
        res = res + '?' + app_conf('eor.static-serial')

    return res
