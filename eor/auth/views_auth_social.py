#coding: utf-8

import logging
log = logging.getLogger(__name__)

import datetime

from urllib import urlencode
from urlparse import parse_qs
from collections import OrderedDict

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config

from sqlalchemy.orm.exc import NoResultFound

from rauth import OAuth1Service
import requests

from sforms import SmallForm, StringField
import colander

from .authentication import SessionUser, login_user, logout_user
from .utils import (login_validator, user_email_unique, user_login_unique,
                    user_can_login)

from .. import models
from eor_settings import get_setting
from ..render import add_flash_message  # TODO


def handle_login_error(request, message_id, detail=None):
    add_flash_message(request, message_id, detail=detail)
    return HTTPFound(location=request.route_path('login'))


@view_config(route_name='register-social', renderer='victoria.auth:templates/register-social.mako')
def register_with_social_account(request):

    c = request.tmpl_context

    # if user is already logged in, redirect to referer
    if SessionUser.get(request):
        return HTTPFound(location = '/')  # TODO redirect_to('REFERER', request))

    form = SmallForm()
    StringField(form, 'login',  required=True, validators=[login_validator, user_login_unique])
    StringField(form, 'email',  required=True, validators=[colander.Email(u'Неправильный формат email адреса'), user_email_unique])
    StringField(form, 'name',   required=True)

    ##

    if not 'social-session' in request.session:
        log.warn(u'register_with_social_account(): no social account info in user session')
        return HTTPFound(location = '/')
    session = request.session['social-session']

    ##

    if request.method == 'GET':
        c.form = form.from_object(login=session['login'], name=session['real-name'])
        return dict()

    ##

    if request.method == 'POST':
        c.form = form.from_submitted(request.POST.items())
        if not c.form.valid:
            return dict()

        user = models.User(
            login     = c.form.login.value,
            email     = c.form.email.value,
            name      = c.form.name.value,
            status    = models.User.ACTIVE
        )

        if 'twitter' in session:
            s = session['twitter']
            user.save_twitter_session(s['user-id'], s['access-token'], s['secret'])

        if 'facebook' in session:
            s = session['facebook']
            user.save_facebook_session(s['user-id'], s['access-token'], s['expires'])

        if 'vkontakte' in session:
            s = session['vkontakte']
            user.save_vkontakte_session(s['user-id'], s['access-token'])

        user.add()  # TODO errors!

        del request.session['social-session']

        add_flash_message(request, 'logged-in')

        return HTTPFound(
            location = '/', # TODO c.form.came_from.value or DEFAULT_REDIRECT_TO,
            headers = login_user(request, user)
        )

    # neither GET nor POST
    return HTTPNotFound()


def login_via_social_account(request, get_user_by_social_id, save_session, session_into_session):
    if request.user:

        ## user is logged in: connect social account

        try:
            user = models.User.get_by_id(request.user.id)
        except NoResultFound:
            log.warn(u'user entity not found, logging user out, id {0}'.format(request.user.id))
            return HTTPFound(location='/', headers=logout_user(request))

        try:
            user2 = get_user_by_social_id()
            if user != user2:
                log.warn(u'other user already has this social id: offending user {0}, other user {1}'.format(request.user.id, user2.id))
                return handle_login_error(request, 'other-user-has-same-social-id')
        except NoResultFound:
            pass

        # TODO check if user is blocked?

        save_session(user)
        request.user.update_from_entity(user)

        log.info('added social account for user {0}'.format(user.id))
        add_flash_message(request, 'added-social-account')

        return HTTPFound('/') # TODO redirect

    else:

        ## user is not logged in: either log the user in or redirect to registration

        try:
            user = get_user_by_social_id()
        except NoResultFound:
            # no user with this social id -> redirect to registration
            session_into_session()
            return HTTPFound(request.route_path('register-social'))

        if not user_can_login(user, request):
            return handle_login_error(request, 'bad-login')

        save_session(user)

        log.info('authenticated via social network, user {0}'.format(user.id))
        add_flash_message(request, 'logged-in')

        return HTTPFound(
            location = '/', # TODO redirect where? will redirect_to() work?
            headers = login_user(request, user)
        )


##
## login via twitter
## https://dev.twitter.com/docs/auth/implementing-sign-twitter
##

def get_twitter_oauth_service():
    return OAuth1Service(
        name='twitter',
        consumer_key      = app_conf('twitter-api-key'),
        consumer_secret   = app_conf('twitter-api-secret'),
        request_token_url = 'https://api.twitter.com/oauth/request_token',
        access_token_url  = 'https://api.twitter.com/oauth/access_token',
        authorize_url     = 'https://api.twitter.com/oauth/authorize',
        base_url          = 'https://api.twitter.com/1.1/'
    )


@view_config(route_name='twitter-login')
def twitter_login(request):

    # TODO check if user already has a twitter session

    twitter = get_twitter_oauth_service()

    # 1. get request tokens, set callback url
    #    check oauth_callback_confirmed=true
    #    store request token w/ secret

    # TODO send oauth_callback !!!
    try:
        request_token, request_token_secret = twitter.get_request_token(params={'oauth_callback': request.route_url('twitter-login-cb')})
    except (RequestException, KeyError), e:
        # KeyError seems to be raised when api key/secret is wrong
        log.warn(u'twitter_login: error getting request tokens: {0}'.format(e))
        return handle_login_error(request, 'social-error')

    request.session['twitter-request-secret'] = request_token_secret
    log.debug(u'twitter_login: request_token={rt}, request_token_secret={rts}'.format(rt=request_token, rts=request_token_secret))

    # 2. redirect to twitter.get_authorize_url(request_token)

    authorize_url = twitter.get_authorize_url(request_token)
    return HTTPFound(authorize_url)


@view_config(route_name='twitter-login-cb')
def twitter_login_callback(request):
    # 3. convert request token to access token
    #    request will contain request token and oauth_verifier
    #    fetch secret for the request token from db for signing?
    #    send it and request token to get access token + secret
    #    save access token + secret to database
    # n. redirect to whatever url

    try:
        request_token = request.GET['oauth_token']
        oauth_verifier = request.GET['oauth_verifier']
        log.debug(u'twitter_login_callback: called with request_token={rt}, oauth_verifier={ov}'.format(rt=request_token, ov=oauth_verifier))
    except KeyError, e:
        log.warn(u'twitter_login_callback: request parameter not present: {0}'.format(e))
        return handle_login_error(request, 'social-error')

    try:
        request_token_secret = request.session['twitter-request-secret']
        del request.session['twitter-request-secret']
    except KeyError, e:
        log.warn(u'twitter_login_callback: no twitter-request-secret in session: {0}'.format(e))
        return handle_login_error(request, 'social-error')

    log.debug(u'twitter_login_callback: getting access tokens, request_token={rt}, request_token_secret={rs}'.format(rt=request_token, rs=request_token_secret))
    try:
        session = get_twitter_oauth_service().get_auth_session(
            request_token, request_token_secret,
            method='POST', data={'oauth_verifier': oauth_verifier}
        )
    except Exception, e:
        log.warn(u'twitter_login_callback: error requesting access tokens: {0}'.format(e))
        return handle_login_error(request, 'social-error')

    log.debug(u'twitter_login_callback: access_token={at}, access_token_secret={ats}'.format(at=session.access_token, ats=session.access_token_secret))

    req = session.get('account/verify_credentials.json', params={'skip_status': 'true'}, verify=True)
    json = req.json()
    twitter_user_id = json['id_str']
    screen_name = json.get('screen_name', u'')
    real_name = json.get('name', u'')
    log.debug(u'twitter_login_callback: verify_credentials: user_id={id}, screen_name={sn}'.format(id=twitter_user_id, sn=screen_name))

    ## login logic

    def get_user_by_twitter_id():
        return models.User.get_by_twitter_id(twitter_user_id)

    def save_twitter_session(user):
        user.save_twitter_session(twitter_user_id, session.access_token, session.access_token_secret)

    def twitter_session_into_session():
        request.session['social-session'] = {
            'twitter': {
                'user-id': twitter_user_id,
                'access-token': session.access_token,
                'secret': session.access_token_secret,
            },
            'login': screen_name,
            'real-name': real_name
        }

    return login_via_social_account(request, get_user_by_twitter_id, save_twitter_session, twitter_session_into_session)


##
## login via facebook
##

@view_config(route_name='facebook-login')
def facebook_login(request):
    query_string = urlencode(OrderedDict(
        client_id     = app_conf('facebook-app-id'),
        redirect_uri  = request.route_url('facebook-login-cb'),
        response_type = 'code',
        scope = 'user_status,read_stream'  #  [u'export_stream', u'public_profile', u'read_stream', u'user_status']
    ))
    authorize_url = 'https://www.facebook.com/dialog/oauth?' + query_string
    return HTTPFound(authorize_url)


@view_config(route_name='facebook-login-cb')
def facebook_login_callback(request):
    """
    https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow/
    """

    if 'error' in request.GET:
        log.warn(u'facebook_login_callback(): error = {0}, error_reason = {1}'.format(request.GET['error'], request.GET.get('error_reason')))
        return handle_login_error(request, 'social-error', detail=request.GET.get('error_reason'))

    if 'error_message' in request.GET:
        log.warn(u'facebook_login_callback(): error_code = {0}, error_message = {1}'.format(request.GET.get('error_code'), request.GET.get('error_message')))
        return handle_login_error(request, 'social-error', detail=request.GET.get('error_message'))

    try:
        code = request.GET['code']
    except KeyError, e:
        log.error(u'facebook_login_callback(): "code" parameter is not present')
        return handle_login_error(request, 'social-error', detail= u'"code" parameter is not present')

    log.debug(u'facebook_login_callback(): code = {0}'.format(code))

    ## exchange code for an access token

    resp = requests.get(
        'https://graph.facebook.com/oauth/access_token',
        params = {
            'client_id': app_conf('facebook-app-id'),
            'client_secret': app_conf('facebook-app-secret'),
            'code': code,
            'redirect_uri': request.route_url('facebook-login-cb') # TODO ??
        }
    )

    # TODO [] -> get()
    if resp.headers['content-type'].startswith('application/json'):
        json = resp.json()
        log.error(u'facebook_login_callback(): /oauth/access_token returned error: type = {0}, code = {1}, message: {2}'.format(
            json['error']['type'], json['error']['code'], json['error']['message']
        ))
        return handle_login_error(request, 'social-error', detail=json['error']['message'])

    body_parsed = parse_qs(resp.text)
    try:
        access_token = body_parsed['access_token'][0]
        expires = datetime.datetime.now() + datetime.timedelta(0, int(body_parsed['expires'][0]))
    except (KeyError, ValueError, IndexError), e:
        log.error(u'facebook_login_callback(): error parsing /oauth/access_token response: error = {0}, response: {1}'.format(e, resp.text))
        return handle_login_error(request, 'social-error', detail=resp.text)

    log.debug(u'facebook_login_callback(): access_token = {access_token}, expires = {expires}'.format(
        access_token = access_token, expires = expires
    ))

    ## get user info for the access token
    ## https://developers.facebook.com/docs/graph-api/reference/user/
    ## {u'username': u'pavel.efremov.146', u'first_name': u'Pavel', u'last_name': u'Efremov', u'verified': True, u'name': u'Pavel Efremov', u'locale': u'en_US', u'gender': u'male', u'updated_time': u'2014-03-10T07:32:26+0000', u'link': u'https://www.facebook.com/pavel.efremov.146', u'timezone': 4, u'id': u'100007909573593'}

    resp = requests.get(
        'https://graph.facebook.com/me',
        params = {
            'access_token': access_token
        }
    )

    # TODO what error messages are possible?
    error = resp.json().get('error', resp.json().get('data', {}).get('error'))  # TODO ?
    if error:
        log.error(u'facebook_login_callback(): /me returned error: {0}'.format(error))
        return handle_login_error(request, 'social-error', detail=error)

    # TODO this can also be used to check if user session is valid
    data = resp.json()
    facebook_user_id = data['id']
    login            = data.get('username', u'')
    real_name        = data.get('name', u'')

    # TODO also available: username, name, first_name, last_name, link

    log.debug(u'facebook_login_callback(): facebook user id = {0}, name = {1}, link = {2}'.format(
        facebook_user_id, data['name'], data['link']
    ))

    ## login logic

    def get_user_by_facebook_id():
        return models.User.get_by_facebook_id(facebook_user_id)

    def save_facebook_session(user):
        user.save_facebook_session(facebook_user_id, access_token, expires)

    def facebook_session_into_session():
        request.session['social-session'] = {
            'facebook': {
                'user-id': facebook_user_id,
                'access-token': access_token,
                'expires': expires
            },
            'login': login,
            'real-name': real_name
        }

    return login_via_social_account(request, get_user_by_facebook_id, save_facebook_session, facebook_session_into_session)


##
## login via vkontakte
## https://vk.com/dev/auth_sites  https://vk.com/apps?act=manage
##

@view_config(route_name='vkontakte-login')
def vkontakte_login(request):
    query_string = urlencode(OrderedDict(
        client_id      = app_conf('vkontakte-app-id'),
        redirect_uri   = request.route_url('vkontakte-login-cb'),  # TODO ???
        display        = 'page',
        response_type  = 'code',
        scope          = 'status,offline', # 'photos,notes,status,wall,offline',
        v              = '5.14'
    ))
    authorize_url = 'http://oauth.vk.com/authorize?' + query_string
    return HTTPFound(authorize_url)


@view_config(route_name='vkontakte-login-cb')
def vkontakte_login_callback(request):

    if 'error' in request.GET:
        log.warn(u'vkontakte_login_callback(): login error: error = {0}, error_description = {1}'.format(
            request.GET.get('error'), request.GET.get('error_description')
        ))
        return handle_login_error(request, 'social-error', detail=request.GET.get('error_description', u''))

    try:
        code = request.GET['code']
        log.debug(u'vkontakte_login_callback(): code={0}'.format(code))
    except KeyError, e:
        log.error(u'vkontakte_login_callback(): "code" parameter not present')
        return handle_login_error(request, 'social-error', detail=u'параметр "code" не передан')

    resp = requests.post(
        'https://oauth.vk.com/access_token',
        data = {
            'client_id':     app_conf('vkontakte-app-id'),
            'client_secret': app_conf('vkontakte-app-secret'),
            'code':          code,
            'redirect_uri':  request.route_url('vkontakte-login-cb') # TODO ???
        }
    )

    try:
        json = resp.json()
    except ValueError, e:
        log.error(u'vkontakte_login_callback(): /oauth/access_token: not json, response = {0}'.format(resp.text))
        return handle_login_error(request, 'social-error', detail=resp.text)

    if 'access_token' in json:
        access_token = json['access_token']
        vkontakte_user_id = json['user_id']
        login = json.get('username', u'')
        real_name = json.get('full_name', u'')
        log.debug(u'vkontakte_login_callback(): /oauth/access_token: access_token = {0}, user_id = {1}, resp = {2}'.format(
            access_token, vkontakte_user_id, json
        ))
    else:
        # {"error":"invalid_grant","error_description":"Code is invalid or expired."}
        log.error(u'vkontakte_login_callback(): /oauth/access_token: no access_token, response = {0}'.format(resp.text))
        return handle_login_error(request, 'social-error', detail=resp.text)

    ## login logic

    def get_user_by_vkontakte_id():
        return models.User.get_by_vkontakte_id(vkontakte_user_id)

    def save_vkontakte_session(user):
        user.save_vkontakte_session(vkontakte_user_id, access_token)

    def vkontakte_session_into_session():
        request.session['social-session'] = {
            'vkontakte': {
                'user-id': vkontakte_user_id,
                'access-token': access_token
            },
            'login': login,
            'real-name': real_name
        }

    return login_via_social_account(request, get_user_by_vkontakte_id, save_vkontakte_session, vkontakte_session_into_session)
