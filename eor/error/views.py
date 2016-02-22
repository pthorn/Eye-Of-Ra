# coding: utf-8

import logging
log = logging.getLogger(__name__)

# according to http://docs.pylonsproject.org/projects/pyramid/en/latest/api/exceptions.html ,
# Forbidden = alias of HTTPForbidden, NotFound = alias of HTTPNotFound
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.renderers import render_to_response

from ..config import config
from ..models import Session
from ..render import render_message


# http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/views.html#using-special-exceptions-in-view-callables
# http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/webob.html#exception-responses
# http://docs.pylonsproject.org/projects/pyramid/en/latest/api/httpexceptions.html#module-pyramid.httpexceptions
#
# HTTPException: detail. comment
#
# 401 vs. 403 http://danielirvine.com/blog/2011/07/18/understanding-403-forbidden/


def not_found(context, request):
    #Session.rollback() # avoids "current transaction is aborted"
    return render_message('404', subst=dict(detail=context.detail), status=404, request=request)


def not_found_xhr(context, request):
    json = {
        'status': 'http-error',
        'http_status': 404,
        'code': u'not-found'
    }

    return render_to_response('json', json, request=request,
                              response=Response(status=404))


def forbidden(context, request):
    log.debug(u'forbidden: path %s, result %s', request.path, request.exception.result)

    if request.user:
        return render_message('forbidden', subst=dict(), status=403, request=request)
    else:
        if config.forbidden_show_login_handler is not None:
            return config.forbidden_show_login_handler(context, request)
        else:
            return HTTPFound(location=request.route_path('login', _query=(('rto', request.path),)))


def forbidden_xhr(context, request):
    log.debug(u'forbidden: path %s, result %s', request.path, request.exception.result)

    http_status = 401 if request.user else 403

    json = {
        'status': 'http-error',
        'http_status': http_status,
        'code': u'forbidden' if request.user else 'unauthorized'
    }

    return render_to_response('json', json, request=request,
                              response=Response(status=http_status))


def url_decode_error(context, request):

    log.warning('URLDecodeError: %s [%s>>%s<<%s], url = %s, user agent = %s' % (
        context, context.object[:context.start], context.object[context.start:context.end], context.object[context.end:],
        request.url, request.user_agent))

    Session.rollback()  # avoids "current transaction is aborted"
    return render_message('url-decode-error', status=400, request=request)


def internal_error(context, request):
    Session.rollback() # avoids "current transaction is aborted"
    if request.is_xhr:
        json = {'status': 'error', 'message': u'500'}  # TODO
        return render_to_response('json', json, request=request)
    else:
        return render_message('500', status=500, request=request)
