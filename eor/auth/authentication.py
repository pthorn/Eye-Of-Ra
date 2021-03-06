# coding: utf-8

import logging
log = logging.getLogger(__name__)

import datetime

from pyramid.security import authenticated_userid, remember, forget

from sqlalchemy.orm.exc import NoResultFound

from . import settings


def configure(config):
    from pyramid.authentication import SessionAuthenticationPolicy
    from pyramid.events import NewRequest

    authn_policy = SessionAuthenticationPolicy(
        callback=get_principals_for_userid_callback,
        debug=False
    )
    config.set_authentication_policy(authn_policy)

    config.add_request_method(request_get_user, 'user', reify=True)
    config.add_subscriber(update_activity, NewRequest)


def get_principals_for_userid_callback(userid, request):
    """
    expected to return None if the userid doesn’t exist or a sequence of principal identifiers (possibly empty) if the user does exist
    """
    return [] if request.user else None


def request_get_user(request):
    """
    reified request property request.user
    """
    return settings.session_class.get(request)


def update_activity(event):
    """
    NewRequest listener
    http://docs.pylonsproject.org/docs/pyramid/en/1.5-branch/api/events.html#pyramid.events.NewRequest
    """
    # TODO check for nonexistent & disabled user when updating from entity!?
    user = event.request.user
    if user:
        user.update_activity()


##
## lightweight user object
##

class SessionUser(object):
    '''
    An object representing an authenticated user.

    Is placed into session in login() - TODO not updated when user details are updated
    Does not store authorization information.

    For tracking last activity time, time of last database update is stored.
     if that time is > 5 min ago, write to the database and reset it.
    '''

    SESSION_KEY = 'user'
    ACTIVITY_UPDATE_MIN = 5

    def __init__(self, request, user_entity):
        """
        creates new SessionUser object and puts it into session
        should only be called when logging user in
        """

        self.id = None
        self.real_name = None

        user_entity.update_last_login()

        self.last_activity_update = datetime.datetime.min
        user_entity.update_last_activity()

        self.update_from_entity(user_entity)

        request.session[self.SESSION_KEY] = self  # place self into session

    @classmethod
    def get(cls, request):
        """
        SessionUser.get(request) -> SeesionUser object for current user or None
        """
        return request.session.get(cls.SESSION_KEY)

    def get_entity(self):
        try:
            return settings.user_model.get_by_id(self.id)
        except NoResultFound:
            log.warn(u'SessionUser.get_entity(): entity not found, id %s', self.id)
            # TODO!! entity does not exist -> log user out!

    def update_from_entity(self, user_entity):
        """
        id must be available as user_entity.id
        """
        self.id = user_entity.id
        self.real_name = user_entity.name or user_entity.login

    def update_activity(self):
        """
        update last activity time in database if it's older than n minutes
        """
        if datetime.datetime.now() - self.last_activity_update > datetime.timedelta(minutes=self.ACTIVITY_UPDATE_MIN):
            log.debug('update_activity(), id %s', self.id)
            user_entity = self.get_entity()

            user_entity.update_last_activity()
            self.last_activity_update = datetime.datetime.now()

            self.update_from_entity(user_entity)  # update user details in case they changed

            # TODO session.changed()!

    def has_role(self, role_id):
        return settings.user_model.has_role(self.id, role_id)

    # TODO memoize somehow?
    def has_permission(self, permission, object_type, object_id=None):
        return settings.user_model.has_permission_for_object_type(permission, object_type, object_id)

    def __unicode__(self):
        return u'User(id={id}, email={email}, real_name={real_name}'.format(
            id = self.id,
            email = self.email,
            real_name = self.real_name
        )


##
## for use in login/logout views
##

def login_user(request, user_entity):
    """
    log user in
    note: this function does no checks!
    :return headers
    """
    session_user = settings.session_class(request, user_entity)  # put SessionUser into session
    log.info(u'login, user %s, ip %s' % (user_entity.id, request.ip))
    return remember(request, session_user.id)


def logout_user(request):
    """
    log user out, end the session
    :return http headers
    """
    if not request.user:
        return None

    log.info(u'logout, user: %s' % (request.user.id, ))
    request.session.invalidate()
    return forget(request)
