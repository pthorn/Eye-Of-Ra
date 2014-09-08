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

from . import Base, Session, BaseMixin
from ..utils.config import app_conf

from .user_mixins import UserModelMixin, SocialMixin


class Role(Base, BaseMixin):

    __tablename__ = 'roles'

    id             = Column(Unicode, primary_key=True)
    name           = Column(Unicode)
    description    = Column(Unicode)

    _rest_search_columns = [id, name, description]

    @classmethod
    def get_all(cls):
        return Session.query(cls).order_by(cls.name).all()

    @classmethod
    def get_for_rest_grid(cls, start=0, limit=None, order=None, search=None, filters=None, query=None):
        '''
        special filter value: e_user_login
        '''
        if filters and 'e_user_login' in filters:
            q = (Session.query(cls)
                .join(cls.users)
                .options(contains_eager(cls.users))
                .filter(User.login == filters['e_user_login'])
            )
            del filters['e_user_login']
        else:
            q = None

        return super(Role, cls).get_for_rest_grid(start, limit, order, search, filters, q)


user_role_link = Table(
    'user_role_link',   Base.metadata,
    Column('user_login', Unicode, ForeignKey('users.login'), primary_key=True),
    Column('role_id',    Integer, ForeignKey('roles.id'),    primary_key=True)
)


class RolePermission(Base, BaseMixin):

    __tablename__ = 'role_permissions'

    role_id        = Column(Unicode, ForeignKey('roles.id'), primary_key=True)
    object_type    = Column(Unicode)
    object_id      = Column(Unicode)
    permission     = Column(Unicode, primary_key=True)

    role = relationship(Role, backref="permissions")


#user_status_choices = [(u'UNCONFIRMED', u'Не подтвержден'), (u'ACTIVE', u'Активен'), (u'DISABLED', u'Заблокирован')]

class User(Base, BaseMixin, UserModelMixin, SocialMixin):

    __tablename__ = 'users'

    login          = Column(Unicode, primary_key=True)
    email          = Column(Unicode)  # unique

    password_hash  = Column(Unicode, server_default='')
    confirm_code   = Column(Unicode)
    confirm_time   = Column(DateTime)

    status         = Column(Unicode)

    name           = Column(Unicode)

    avatar_date    = Column(DateTime, server_default='')

    registered     = Column(DateTime, FetchedValue())
    last_login     = Column(DateTime)
    last_activity  = Column(DateTime)

    comment        = Column(Unicode)

    roles = relationship(Role, secondary=user_role_link, backref="users")

    _rest_search_columns = [login, name, email]

    # status
    UNCONFIRMED    = 'UNCONFIRMED'
    DISABLED       = 'DISABLED'
    ACTIVE         = 'ACTIVE'
    PASSWORD_RESET = 'PASSWORD_RESET'

    def __init__(self, **kwargs):
        self.contacts = u''
        self.comment = u''
        self.groups = u''
        self.confirm_code = u''
        super(User, self).__init__(**kwargs)

    @property
    def id(self):
        """
        for auth
        """
        return self.login

    @classmethod
    def get_by_login(cls, login):
        return Session.query(cls)\
            .filter(func.lower(cls.login) == login.lower())\
            .one()

    @classmethod
    def get_by_id(cls, login):
        return cls.get_by_login(login)

    @classmethod
    def get_by_email(cls, email):
        return Session.query(cls)\
            .filter(func.lower(cls.email) == email.lower())\
            .one()

    @classmethod
    def get_permissions_for_object_type(cls, user_id, object_type, object_id=None):
        q = (Session.query(RolePermission)
            .join(RolePermission.role, Role.users)
            .options(contains_eager(RolePermission.role, Role.users))
            .filter(RolePermission.object_type == object_type)
            .filter(User.login == user_id))
        if object_id:
            q = q.filter(or_(RolePermission.object_id == object_id, RolePermission.object_id == u''))
        return q.all()

    @classmethod
    def has_permission_for_object_type(cls, user_id, permission, object_type, object_id=None):
        q = (Session.query(RolePermission)
            .join(RolePermission.role, Role.users)
            .options(contains_eager(RolePermission.role, Role.users))
            .filter(RolePermission.object_type == object_type)
            .filter(RolePermission.permission == permission)
            .filter(User.login == user_id))
        if object_id:
            q = q.filter(or_(RolePermission.object_id == object_id, RolePermission.object_id == u''))
        xx = q.first()
        return xx is not None # q.first() is not None

    @classmethod
    def has_role(cls, user_id, role_id):
        q = (Session.query(Role)
            .join(Role.users)
            .options(contains_eager(Role.users))
            .filter(User.login == user_id)
            .filter(Role.id == role_id))
        xx = q.first()
        return xx is not None # q.first() is not None

    @classmethod
    def get_by_confirm_code(cls, confirm_code):
        return Session.query(cls)\
            .filter(cls.confirm_code == confirm_code)\
            .one()

    def generate_and_set_confirm_code(self):
        import random
        bytes = 16
        self.confirm_code = hex(random.getrandbits(bytes*8))[2:-1]
        self.confirm_time = datetime.datetime.now()
        return self.confirm_code

    @classmethod
    def get_choices(cls):
        """
        for a form select field
        [(id, name), ...]
        """
        # TODO support filtering for autocomplete widget
        return Session.query(cls.login, cls.name).order_by(cls.login).all()

    #@classmethod
    #def get_all(cls):
    #    return Session.query(cls).order_by(cls.login).all()
    #
    #@classmethod
    #def get_choices_for_m2m(cls):
    #    res = cls.get_all()
    #    #return [(obj.id, obj.name)  for obj in res]
    #    return [( [(obj.login, obj.login)  for obj in res], u'AAA') ]
