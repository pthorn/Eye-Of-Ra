
"""
    appconf parameters
        captcha-font-path
        captcha-font-size
        captcha-valid-minutes

    TODO

        - captcha is generated when captcha image is requested, is this ok?
        - regenerate captcha! if user can't read old one
        - store captcha in redis rather than database
"""


from .field import CaptchaField


def includeme(config):

    from ..utils.config import parse_app_settings

    settings = config.get_settings()

    parse_app_settings(settings, {
        'captcha-font-path':     dict(convert=unicode, default='../captcha-fonts'),
        'captcha-font-size':     dict(convert=int, default=36),
        'captcha-distortion-x':  dict(convert=int, default=20),
        'captcha-distortion-y':  dict(convert=int, default=25),
        'captcha-valid-minutes': dict(convert=int, default=15)
    })

    config.add_route('captcha-image',          R'/eor/captcha-image',            request_method='GET')
    config.add_route('captcha-image-w-formid', R'/eor/captcha-image/{form_id}',  request_method='GET')

    config.scan('.views')
