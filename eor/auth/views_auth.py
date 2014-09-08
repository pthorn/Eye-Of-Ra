#coding: utf-8

import logging
log = logging.getLogger(__name__)

import datetime
import urlparse

from sqlalchemy.orm.exc import NoResultFound
import transaction

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config

import colander

from sforms import SmallForm, StringField

from .utils import (login_validator, passwords_match, user_email_unique, user_login_unique)
from .authentication import SessionUser, login_user, logout_user

from .import settings
from .. import models
from ..utils import app_conf
from ..render import add_flash_message
from ..utils import send_auto_email, EmailException
#from ..utils.template import render_auto_page


class LoginViews(object):

    def __init__(self, request):
        self.request = request
        self.c = request.tmpl_context

    def redirect_to(self, came_from):
        """
        """
        DEFAULT_REDIRECT_TO = '/'

        if came_from == 'REFERER':
            came_from = self.request.referer

        return came_from if came_from else DEFAULT_REDIRECT_TO

    # TODO this is authorization
    def user_can_login(self, user):
        if user.status != 'ACTIVE':
            log.info(u'login failed: %s: status %s, ip %s' % (login, user.status, self.request.ip))
            return False
        return True

    def get_login_form(self):
        form = SmallForm(request=self.request)
        StringField(form, 'login',      required=True)
        StringField(form, 'password',   required=True)
        StringField(form, 'came_from')
        return form

    def login_get(self):
        c = self.c

        login = self.request.session.pop('login', '')
        came_from = self.request.GET.get('rto', self.request.referer)

        c.form = self.form.from_object(
            login=login,
            came_from=came_from
        )

        return dict()

    def login_post(self):
        c = self.c
        request = self.request

        c.form = self.form.from_request(request)
        if not c.form.valid:
            return dict()

        try:
            user = settings.user_model.get_by_id(c.form.login.value.strip().lower())  # TODO will get_by_id work with lowercase id?
        except NoResultFound:
            log.info('login failed: %s: no such user, ip %s' % (c.form.login.value, request.ip))
            add_flash_message(request, 'bad_login')
            return dict()

        if not user.check_password(c.form.password.value):
            log.info(u'login failed: bad password, user %s, ip %s' % (c.form.login.value, request.ip))
            add_flash_message(request, 'bad_login')
            return dict()

        if not self.user_can_login(user):
            log.info(u'login failed: user %s, status %s, ip %s' % (c.form.login.value, user.status, request.ip))
            add_flash_message(request, 'bad_login')
            return dict()

        # successful login

        add_flash_message(request, 'logged_in')

        return HTTPFound(
            location = self.redirect_to(c.form.came_from.value),
            headers = login_user(request, user)
        )

    #@view_config(route_name='login', renderer='victoria.auth:templates/login.mako')
    def login(self):
        """
        login view: log in with username & password
        request.session['login'] is used as the initial value of the login field if exists
        """
        # TODO spaces / case sensitivity in login?

        c = self.c
        request = self.request

        # if user is already logged in, redirect to referer
        if SessionUser.get(request):
            return HTTPFound(location=self.redirect_to('REFERER'))

        self.form = self.get_login_form()

        if request.method == 'GET':
            return self.login_get()

        if request.method == 'POST':
            return self.login_post()

        # neither GET nor POST
        return HTTPNotFound()

    #@view_config(route_name='logout')
    def logout(self):
        headers = logout_user(self.request)
        return HTTPFound(location=self.request.referer or '/', headers=headers)


###
### user registration
###

@view_config(route_name='register', renderer='victoria.auth:templates/register.mako')
def register(request):

    if request.user: # user is already logged in
        return HTTPFound(location='/')

    c = request.tmpl_context

    form = SmallForm(validators=[passwords_match])
    StringField(form, 'login',      required=True, validators=[login_validator, user_login_unique])
    StringField(form, 'email',      required=True, validators=[
        colander.Email(u'Неправильный формат email адреса'), user_email_unique()
    ])
    StringField(form, 'name',       required=True)
    StringField(form, 'password1',  required=True)
    StringField(form, 'password2',  required=True)

    if request.method == 'GET':
        c.form = form.from_object()
        return dict()

    if request.method == 'POST':
        c.form = form.from_submitted(request.POST.items())
        if not c.form.valid:
            # passwords_match
            if c.form.error:
                c.form._errors['password1'] = c.form.error
                c.form._errors['password2'] = c.form.error
            return dict()

        user = settings.user_model(
            id        = c.form.login.value,
            email     = c.form.email.value,
            real_name = c.form.name.value,
            status    = settings.user_model.UNCONFIRMED
        )
        user.set_new_password(c.form.password1.value)
        user.add() # TODO commit? to avoid sending emails in case of database error

        confirm_code = user.generate_and_set_confirm_code()

        try:
            send_auto_email(user.email, 'user-registered', dict(
                user  = user,
                url   = request.route_url('confirm-user', code=confirm_code)
            ))
            return render_auto_page('user-registered', request, dict(user=user))
        except EmailException, e:
            transaction.doom()
            return render_auto_page('error-sending-email', request, dict(email=c.form.email.value))

    # neither GET nor POST
    return HTTPNotFound()


@view_config(route_name='confirm-user')
def confirm(request):
    if SessionUser.get(request): # user already logged in
        return HTTPFound(location='/')

    code = request.matchdict['code']
    try:
        user = settings.user_model.get_by_confirm_code(code)
    except NoResultFound:
        log.info('unknown confirm code %s' % code)
        raise HTTPNotFound()

    if user.status != settings.user_model.UNCONFIRMED:
        log.warn('expected status UNCONFIRMED, user %s has status %s' % (user.login, user.status))
        raise HTTPNotFound()

    if datetime.datetime.now() - user.confirm_time > datetime.timedelta(hours=48):
        user.delete()
        # TODO confirm_time check! if time check failed, delete user?
        raise HTTPNotFound() # TODO redirect to / ?

    user.status = settings.user_model.ACTIVE
    user.confirm_code = ''
    user.confirm_time = None

    return HTTPFound(location=request.route_path('login', _query=dict(confirmed=user.id)))


###
### password reset
###

@view_config(route_name='reset-password', renderer='victoria.auth:templates/reset-password.mako')
def reset_password(request):
    c = request.tmpl_context

    if request.user:  # user already logged in
        return HTTPFound(location=DEFAULT_REDIRECT_TO)

    def user_valid(node, value):
        try:
            user = settings.user_model.get_by_email(value)
            if user.status == settings.user_model.DISABLED:
                raise colander.Invalid(node, u'Пользователь заблокирован.')
        except NoResultFound:
            raise colander.Invalid(node, u'Пользователь с таким email адресом у нас не зарегистрирован.')

    reset_form = SmallForm()
    StringField(reset_form, 'email', required=True, validators=[colander.Email(u'Неправильный формат email адреса'), user_valid])

    if request.method == 'GET':
        c.form = reset_form.from_object()
        return dict()

    if request.method == 'POST':
        c.form = reset_form.from_submitted(request.POST.items())
        if not c.form.valid:
            if (c.form.email.error or u'').find(u'заблокирован') != -1:
                c.user_blocked = True
            return dict()

        try:
            user = settings.user_model.get_by_email(c.form.email.value)
        except NoResultFound:
            raise HTTPNotFound() # TODO!
        if user.status == settings.user_model.DISABLED:
            raise HTTPNotFound() # TODO!

        confirm_code = user.generate_and_set_confirm_code()

        try:
            send_auto_email(user.email, 'password-reset', dict(
                user = user,
                url = request.route_url('reset-password-do', code=confirm_code)
            ))
            return render_auto_page('reset-email-sent', request, dict(user=user))
        except EmailException, e:
             c.message = u'Ошибка: ' + unicode(e) # TODO!

    # neither GET nor POST
    return HTTPNotFound()


@view_config(route_name='reset-password-do', renderer='victoria.auth:templates/reset-password-do.mako')
def reset_password_do(request):
    c = request.tmpl_context

    if SessionUser.get(request): # user already logged in
        return HTTPFound(location=DEFAULT_REDIRECT_TO)

    def passwords_match(node, value):
        if node.get_value(value, 'new_password_1') != node.get_value(value, 'new_password_2'):
            raise colander.Invalid(node, u'Пароли не совпадают')

    password_change_form = SmallForm(validators=[passwords_match])
    StringField(password_change_form, 'login',           required=True)
    StringField(password_change_form, 'new_password_1',  required=True)
    StringField(password_change_form, 'new_password_2',  required=True)

    code = request.matchdict['code']

    try:
        user = settings.user_model.get_by_confirm_code(code)
    except NoResultFound:
        raise HTTPNotFound() # TODO redirect to / ?

    if user.confirm_time is None:
        raise HTTPNotFound() # TODO redirect to / ?

    if datetime.datetime.now() - user.confirm_time > datetime.timedelta(hours=48):
        raise HTTPNotFound() # TODO redirect to / ?

    if request.method == 'GET':
        c.form = password_change_form.from_object()
        return dict()

    if request.method == 'POST':
        c.form = password_change_form.from_submitted(request.POST.items())
        if not c.form.valid:
            # passwords_match
            if c.form.error:
                c.form._errors['new_password_1'] = c.form.error
                c.form._errors['new_password_2'] = c.form.error
            return dict()

        if user.id != c.form.login.value:
            raise HTTPNotFound() # TODO !?

        if user.status == settings.user_model.UNCONFIRMED:
            user.status = settings.user_model.ACTIVE
        user.confirm_code = ''
        user.confirm_time = None
        user.set_new_password(c.form.new_password_1.value)

        return HTTPFound(location=request.route_path('login', _query=dict(reset=user.id)))

    # neither GET nor POST
    return HTTPNotFound()
