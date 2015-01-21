# coding: utf-8

import logging
log = logging.getLogger(__name__)

from .sqlalchemy_base import Session, Base
from .cms import CMSMessage, Page
from .user import Role, User


def includeme(config):
    settings = config.get_settings()
    from .sqlalchemy_base import initialize_sqlalchemy
    initialize_sqlalchemy(settings)


__all__ = [
    includeme,
    Session, Base,
    Page,
    CMSMessage,
    Role,
    User
]
