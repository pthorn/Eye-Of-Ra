# coding: utf-8

from .send_email import send_email, send_auto_email, EmailException


class AttrDict(dict):
    """
    http://stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute-in-python
    memory leak in python < 2.7.3! http://bugs.python.org/issue1469629
    """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def includeme(config):
    from .request_utils import get_ip
    config.add_request_method(get_ip, 'ip', reify=True)

    from eor_settings import ParseSettings

    (ParseSettings(config.get_settings(), prefix='eor')
        .string('email-from', default='root@localhost')
        .string('smtp-host', default='localhost'))
