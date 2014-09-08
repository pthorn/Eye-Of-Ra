# coding: utf-8

import logging
log = logging.getLogger(__name__)

from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from mako.template import Template

from sqlalchemy.orm.exc import NoResultFound

from . import settings
from ..utils import AttrDict


def render_message(message_id, request, subst=None, status=200):
    """
    render auto page by id
    """

    from .. import models # ?

    c = request.tmpl_context
    subst = subst or dict()

    try:
        c.message = models.CMSMessage.get_by_id(message_id)
    except NoResultFound:
        log.error(u'render_message(): unknown message_id %s' % message_id)
        return HTTPNotFound()

    if subst:
        c.message.expunge() # prevent saving interpolated content to database
        try:
            c.message.content = Template(c.message.content, default_filters=['h']).render_unicode(**subst)
        except KeyError, e: # TODo mako exc!
            log.error(u"render_message(): interpolation error: message_id %s, key %s" % (message_id, unicode(e)))
            return HTTPNotFound()

    response = render_to_response(settings.message_template, dict(), request=request)
    response.status_int = status
    return response


class FlashMessage(object):

    def __init__(self, message_id, queue, **kwargs):
        self.message_id = message_id
        self.queue = queue
        self.params = AttrDict(kwargs)


def add_flash_message(request, message_id, queue=u'', **kwargs):
    request.session.flash(FlashMessage(message_id, queue, **kwargs), queue)
