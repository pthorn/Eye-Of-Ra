
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

    config.add_route('captcha-image',          R'/eor/captcha-image',            request_method='GET')
    config.add_route('captcha-image-w-formid', R'/eor/captcha-image/{form_id}',  request_method='GET')
    config.scan('.views')
