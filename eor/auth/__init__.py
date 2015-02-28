# coding: utf-8


class Settings(object):

    def __init__(self):
        self._user_model = None
        self._session_class = None

    @property
    def user_model(self):
        if not self._user_model:
            from ..models import User
            self._user_model = User
        return self._user_model

    @user_model.setter
    def user_model(self, model):
        self._user_model = model

    @property
    def session_class(self):
        if not self._session_class:
            from .authentication import SessionUser
            self._session_class = SessionUser
        return self._session_class

    @session_class.setter
    def session_class(self, cls):
        self._session_class = cls

settings = Settings()


from .authentication import SessionUser
from .authorization import ebff
from .views_auth import LoginViews


def includeme(config):

    from ..utils.settings import ParseSettings

    (ParseSettings(config.get_settings(), prefix='eor.')
        .bool('debug-auth', default=False))


    # TODO consolidate resource factories
    from pyramid.security import authenticated_userid, Allow, Authenticated, DENY_ALL

    class ResourceFactory(object):
        __acl__ = [
            (Allow, Authenticated, 'auth')
        ]
        def __init__(self, request):
            pass # dynamic acl generation is possible here

    def add(*args, **kwargs):
        kwargs['factory'] = ResourceFactory
        return config.add_route(*args, **kwargs)

    add('login',                 R'/auth/login',                      request_method=['GET', 'POST'])
    add('logout',                R'/auth/logout',                     request_method='GET')

    # TODO request methods?
    add('register',              R'/auth/register',                   request_method=['GET', 'POST'])
    add('confirm-user',          R'/auth/confirm/{code}',             request_method=['GET', 'POST'])
    add('reset-password',        R'/auth/reset-password',             request_method=['GET', 'POST'])
    add('reset-password-do',     R'/auth/reset-password/{code}',      request_method=['GET', 'POST'])

    add('register-social',       R'/auth/register/social',            request_method=['GET', 'POST'])

    add('twitter-login',         R'/auth/login/twitter',              request_method=['GET'])
    add('twitter-login-cb',      R'/auth/login/twitter-callback',     request_method=['GET'])

    add('facebook-login',        R'/auth/login/facebook',             request_method=['GET'])
    add('facebook-login-cb',     R'/auth/login/facebook-callback',    request_method=['GET'])

    add('vkontakte-login',       R'/auth/login/vkontakte',            request_method=['GET'])
    add('vkontakte-login-cb',    R'/auth/login/vkontakte-callback',   request_method=['GET'])

    from . import authentication
    authentication.configure(config)

    from . import authorization
    authorization.configure(config)

    config.scan('.views_auth')

    """
    from . import views
    views.configure(config, ResourceFactory)

    from .views import every_page
    config.add_subscriber(every_page, BeforeRender)

    from . import search
    search.configure(config, ResourceFactory)

    from . import user
    user.configure(config, ResourceFactory)
    """


__all__ = [
    includeme,
    settings,
    SessionUser,
    ebff,
    LoginViews
]
