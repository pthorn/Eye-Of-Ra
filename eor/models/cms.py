# coding: utf-8

import logging
log = logging.getLogger(__name__)

import datetime

from sqlalchemy import Column
from sqlalchemy.schema import Table, ForeignKey, FetchedValue
from sqlalchemy.types import Integer, Unicode, Float, Boolean, Date, DateTime
from sqlalchemy.orm import relationship, backref, joinedload, joinedload_all, contains_eager
from sqlalchemy.sql import and_, or_, not_, text
from sqlalchemy.sql.expression import func, case

from zope.sqlalchemy import mark_changed

from . import Base, Session



class CMSMessage(Base):

    __tablename__ = 'cms_messages'

    id             = Column(Unicode, primary_key=True)
    purpose        = Column(Unicode)

    title          = Column(Unicode)
    content        = Column(Unicode)
    head           = Column(Unicode)

    comment        = Column(Unicode)
    updated        = Column(DateTime, FetchedValue())


class AutoEmailTemplate(Base):

    __tablename__ = 'auto_email_templates'

    id             = Column(Unicode, primary_key=True,             info=dict(label=u'ID',                 grid=True))
    purpose        = Column(Unicode,                               info=dict(label=u'Когда отправляется', grid=True))

    body_type      = Column(Unicode,                               info=dict(label=u'Тип', choices=[('text', u'Текст'), ('html', u'HTML')]))

    subject        = Column(Unicode,                               info=dict(label=u'Название',           grid=True))
    body           = Column(Unicode,                               info=dict(label=u'Текст',              widget='textarea', optional=True))

    comment        = Column(Unicode,                               info=dict(label=u'Комментарий',        widget='textarea', optional=True))
    added          = Column(DateTime, FetchedValue(),              info=dict(label=u'Добавлено',          viewonly=True))
    updated        = Column(DateTime, FetchedValue(),              info=dict(label=u'Изменено',           viewonly=True))

    _grid_name = u'Шаблоны email'
    _form_name = u'Шаблон email'


#     level               text                not null    check (level in ('DEBUG', 'INFO', 'NOTE', 'WARNING', 'ERROR', 'CRITICAL')),

class LogMessage(Base):

    __tablename__ = 'log_messages'

    id             = Column(Integer, primary_key=True,             info=dict(label=u'ID',               grid=True, viewonly=True))
    added          = Column(DateTime, FetchedValue(),              info=dict(label=u'Добавлено',        grid=True, viewonly=True))

    level          = Column(Unicode,                               info=dict(label=u'Уровень',          grid=True, viewonly=True))

    object         = Column(Unicode,                               info=dict(label=u'Объект',           viewonly=True))
    action         = Column(Unicode,                               info=dict(label=u'Действие',         viewonly=True))
    success        = Column(Boolean,                               info=dict(label=u'Успешно',          viewonly=True))
    subsystem      = Column(Unicode,                               info=dict(label=u'Модуль',           grid=True, viewonly=True))
    message        = Column(Unicode,                               info=dict(label=u'Сообщение',        viewonly=True))

    user_login  = Column(Integer, ForeignKey("users.login"),       info=dict(label=u'Пользователь',     viewonly=True))

    ip_addr        = Column(Unicode,                               info=dict(label=u'Модуль',           viewonly=True))
    user_agent     = Column(Unicode,                               info=dict(label=u'Сообщение',        viewonly=True))

    _grid_name = u'События'
    _form_name = u'Событие'

    @classmethod
    def log(cls, request, level, object, action, success, subsystem, message):
        ip_addr = request.xxx # TODO see how nginx deals with it
        user_agent = request.xxx
        log_message = cls(level=level, object=object, action=action, success=success, subsystem=subsystem, message=message)
        log_message.add() # TODO handle exception!


class Page(Base):

    __tablename__ = 'pages'

    id             = Column(Unicode, primary_key=True)

    title          = Column(Unicode)
    content        = Column(Unicode)
    head           = Column(Unicode, server_default='')

    meta_kw        = Column(Unicode, server_default='')
    meta_desc      = Column(Unicode, server_default='')

    status         = Column(Unicode, server_default='DISABLED')

    comment        = Column(Unicode, server_default='')
    added          = Column(DateTime, FetchedValue())
    updated        = Column(DateTime, FetchedValue())

    ACTIVE = 'ACTIVE'
    DISABLED = 'DISABLED'
