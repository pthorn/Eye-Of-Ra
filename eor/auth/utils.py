# coding: utf-8

import logging
log = logging.getLogger(__name__)

from sqlalchemy.orm.exc import NoResultFound

import colander


##
## validators
##

def login_validator(node, value):
    if not all(((c.isalnum() and ord(c) < 128) or c in '-.@_' for c in value)):
        raise colander.Invalid(node, u'имя пользователя содержит недопустимые символы')


def user_login_unique(node, value):
    # TODO old_login like in user_email_unique?

    from .. import models  # TODO move SocialMixin somewhere else so we can import models at the module level?
    try:
        models.User.get_by_id(value)
        raise colander.Invalid(node, u'Пользователь с таким именем уже зарегистрирован.')
    except NoResultFound:
        pass


def user_email_unique(old_email=None):
    """
    check user email doesn't already exist in database
    :param old_email: do not invalidate if value == old_email
    """

    def validator(node, value):
        if old_email == value:
            return  # valid

        from .. import models  # TODO move SocialMixin somewhere else so we can import models at the module level?
        try:
            user = models.User.get_by_email(value)
            raise colander.Invalid(node, u'Пользователь с этим адресом уже зарегистрирован.')
        except NoResultFound:
            pass

    return validator


def passwords_match(node, value):
    if node.get_value(value, 'password1') != node.get_value(value, 'password2'):
        raise colander.Invalid(node, u'Пароли не совпадают')
