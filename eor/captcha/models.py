# coding: utf-8

import logging
log = logging.getLogger(__name__)

import datetime

from sqlalchemy import Column
from sqlalchemy.schema import FetchedValue
from sqlalchemy.types import Integer, Unicode, Boolean, DateTime
from sqlalchemy.orm.exc import NoResultFound
from zope.sqlalchemy import mark_changed

from ..models import Base, BaseMixin, Session

from eor.utils import app_conf


class CaptchaEntity(Base, BaseMixin):

    __tablename__ = 'captcha'

    remote_addr   = Column(Unicode, primary_key=True)
    form_id       = Column(Unicode, primary_key=True)
    value         = Column(Unicode)
    created       = Column(DateTime, FetchedValue())

    @classmethod
    def get(cls, remote_addr, form_id):
        return Session.query(cls).filter(cls.remote_addr==remote_addr).filter(cls.form_id==form_id).one()

    @classmethod
    def delete_expired(cls):
        stmt = "delete from captcha where current_timestamp - created > INTERVAL '%(valid_min)s min'" % dict(valid_min=app_conf('captcha-valid-minutes'))
        Session().connection().execute(stmt)# text(stmt))
        mark_changed(Session())

    def validate(self, value):
        print '\n---- CaptchaEntity.validate:', value, self.value, self.created
        return (self.value.strip().lower() == value.strip().lower() and
            datetime.datetime.now() - self.created <= datetime.timedelta(minutes=app_conf('captcha-valid-minutes')))


class CaptchaWord(Base, BaseMixin):

    __tablename__ = 'captcha_words'

    word          = Column(Unicode, primary_key=True)
    
    @classmethod
    def get_random(cls):
        return Session.query(cls).order_by('random()')[0]
