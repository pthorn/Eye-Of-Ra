# coding: utf-8

import random
import datetime

from passlib.context import CryptContext

from sqlalchemy import Column
from sqlalchemy.types import Unicode, DateTime
from ..models import Session


passlib_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    default="pbkdf2_sha256",
    all__vary_rounds = "10%",
    pbkdf2_sha256__default_rounds = 8000,
)


class UserModelMixin(object):
    """
    mixin for a sqlalchemy user model that supports authentication
    assumes password hash is stored in self.password_hash
    """

    # settings for password generation
    PWD_CHARACTERS = '23456qwertasdfgzxcvbQWERTASDFGZXCVB789yuiophjknmYUIPHJKLNM'
    MIN_PWD_LEN = 6
    MAX_PWD_LEN = 9

    def check_password(self, password):
        """
        check whether password is valid
        :return boolean
        """
        try:
            return passlib_context.verify(password, self.password_hash)
        except ValueError:  # "hash could not be identified" (e.g. hash is empty)
            return False

    def set_new_password(self, password):
        self.password_hash = passlib_context.encrypt(password)
        return self

    def generate_and_set_password(self):
        password = u''.join([random.choice(self.PWD_CHARACTERS) for i in range(random.randint(self.MIN_PWD_LEN, self.MAX_PWD_LEN))])
        self.set_new_password(password)
        return password

    def update_last_login(self):
        self.last_login = datetime.datetime.now()

    def update_last_activity(self):
        self.last_activity = datetime.datetime.now()


class SocialMixin(object):

    twitter_user_id        = Column(Unicode) # NULL, unique
    twitter_access_token   = Column(Unicode,  server_default='')
    twitter_access_secret  = Column(Unicode,  server_default='')

    facebook_user_id       = Column(Unicode) # NULL, unique
    facebook_access_token  = Column(Unicode,  server_default='')
    #facebook_expires       = Column(DateTime) # NULL

    vkontakte_user_id      = Column(Unicode) # NULL, unique
    vkontakte_access_token = Column(Unicode,  server_default='')

    @classmethod
    def get_by_twitter_id(cls, twitter_id):
        return Session.query(cls)\
            .filter(cls.twitter_user_id == twitter_id)\
            .one()

    def save_twitter_session(self, twitter_id, access_token, access_token_secret):
        self.twitter_user_id = twitter_id
        self.twitter_access_token = access_token
        self.twitter_access_secret = access_token_secret

    @classmethod
    def get_by_facebook_id(cls, facebook_id):
        return (Session.query(cls)
            .filter(cls.facebook_user_id == facebook_id)
            .one())

    def save_facebook_session(self, facebook_user_id, access_token, expires):
        self.facebook_user_id = facebook_user_id
        self.facebook_access_token = access_token
        self.facebook_expires = expires

    @classmethod
    def get_by_vkontakte_id(cls, vkontakte_id):
        return (Session.query(cls)
            .filter(cls.vkontakte_user_id == unicode(vkontakte_id))
            .one())

    def save_vkontakte_session(self, vkontakte_user_id, access_token):
        self.vkontakte_user_id = vkontakte_user_id
        self.vkontakte_access_token = access_token
