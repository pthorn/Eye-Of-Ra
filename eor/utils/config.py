# coding: utf-8

"""
  TODO see custom config props in pyramid docs
  TODO get_path with os.path.exists() check
"""

import logging
log = logging.getLogger(__name__)

app_settings = dict()


def app_conf(key):
    """
    return an application setting by key
    """
    try:
        return app_settings[key]
    except KeyError:
        raise RuntimeError('app_conf(): key %s not present in config' % key)


class AppSettingsParseException(Exception):
    pass


def parse_app_settings(settings, template, prefix='app.'):
    """
    call this before using app_conf() for the first time

    def main(global_config, **settings):
        parse_app_settings(settings, {
            'my-setting':   dict(convert=asbool, default=False),
            'my-setting-2': dict(convert=int,    optional=True),
            ...
        })

    valid keywords
        convert  - required, type conversion (int, unicode, also as_bool etc. from this module)
        default  - if key is not present then use this value (optional)
        optional - defaults to False, if key is not present and default
                   is not specified then exception is raised unless this options is True,
                   in which case the value is set to None
        variants - list of permitted values (checked after type conversion using 'convert', optional) 
    """

    global app_settings
    
    for tpl_key, tpl_options in template.iteritems():
        
        settings_key = prefix + tpl_key
        
        if 'convert' not in tpl_options:
             log.warn(u"'convert' not specified for setting %s, assuming unicode" % (tpl_key,))
             tpl_options['convert'] = unicode
             
        if settings_key in settings:
            app_settings[tpl_key] = tpl_options['convert'](settings[settings_key])
        else:
            if 'default' in tpl_options and 'optional' in tpl_options:
                log.warn(u"both 'default' and 'optional' specified for setting %s" % (tpl_key,))
            if 'default' in tpl_options:
                app_settings[tpl_key] = tpl_options['default']
            elif 'optional' in tpl_options:
                app_settings[tpl_key] = None
            else:
                msg = u'required setting %s%s not present in config' % (prefix, tpl_key)
                log.error(msg)
                raise AppSettingsParseException(msg)

        if 'variants' in tpl_options:
            if app_settings[tpl_key] not in tpl_options['variants']:
                msg = u'value for setting %s = %s must be one of %s' % (tpl_key, app_settings[tpl_key], tpl_options['variants'])
                log.error(msg)
                raise AppSettingsParseException(msg)

    for k, v in settings.iteritems():
        if k.startswith(prefix):
            tpl_key = k[len(prefix):]
            if tpl_key not in template:
                log.warn(u'unknown app setting found: %s' % (tpl_key,))

    #from med48.utils.redis_caching import redis_parse_settings
    #redis_parse_settings(app_settings)

    log.info("application settings: %s" % ', '.join(['%s=%s' % (k, v) for k, v in app_settings.iteritems()]))


##
## some type conversions
##

def as_bool(str_val):
    return str_val.lower() in ('true', '1', 'yes')

def as_list(val):
    return val.split()
