# coding: utf-8

import colander

from sforms import Field, _nothing
from sforms.htmlgen import Tag

from .captcha import Captcha


class CaptchaWidget(object):
    """
    """

    def __init__(self, use_data_src):
        self.use_data_src = use_data_src


    def render(self, field, rargs):

        if not isinstance(field, CaptchaField):
            raise ValueError("CaptchaWidget must be attached to a CaptchaField")

        if field.form_id:
            img_url = field.request.route_path('captcha-image-w-formid', form_id=field.form_id)
        else:
            img_url = field.request.route_path('captcha-image')

        img_tag = Tag('img', data_src=img_url) if self.use_data_src else Tag('img', src=img_url)

        return Tag('div', class_='captcha', **rargs).add([
            img_tag,
            Tag('input', type='text', name=field.name)
        ]).render()


class CaptchaValidator(object):

    def __init__(self, field, message=None):
        if not isinstance(field, CaptchaField):
            raise ValueError("CaptchaValidator can only be attached to a CaptchaField")

        self.field = field
        self.message = message or "Неправильный код подтверждения"

    def __call__(self, node, value):
        remote_addr = self.field.request.client_addr
        print('\n---- request.remote_addr:', self.field.request.client_addr)
        if not Captcha.validate(remote_addr, self.field.form_id, value):
            node.raise_invalid(self.message)


class CaptchaField(Field):

    def __init__(self, form, name, form_id, use_data_src=False):
        super(CaptchaField, self).__init__(
            form,
            name,
            colander.String(),
            '',  # default
            _nothing, # missing: always required
            [CaptchaValidator(self)],
            CaptchaWidget(use_data_src)
        )

        self.form_id = form_id


'''
class CaptchaWidget(object):

    def __call__(self, field):

        def random_string(length=8):
            import random, string
            return ''.join(random.choice(string.ascii + string.digits) for x in xrange(length))

        if not isinstance(field, CaptchaField):
            raise ValueError("CaptchaWidget must be attached to a CaptchaField")

        return """\
<img class="captcha" src="%(img_url)s"><br>
<input type="text" name="%(name)s">
""" % dict(img_url=get_current_request().route_path('captcha-image', form_id=field.form_id), name=field.name) #, _query=dict(nocache=random_string())))
'''

'''
class CaptchaField(TextField):

    widget = CaptchaWidget()

    def __init__(self, label="", form_id="", **kwargs):
        super(CaptchaField, self).__init__(label, [CaptchaValidator()], **kwargs)
        self.form_id = form_id
        self.remote_addr = get_current_request().remote_addr
'''

'''
class CaptchaValidator(object):

    def __init__(self, message=None):
        self.message = message or u"Неправильный код подтверждения"

    def __call__(self, form, field):
        if not isinstance(field, CaptchaField):
            raise ValueError, "CaptchaValidator can only be attached to a CaptchaField"

        if not Captcha.validate(field.remote_addr, field.form_id, field.data):
            raise ValidationError(self.message)
'''
