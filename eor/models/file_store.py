# coding: utf-8

import logging
log = logging.getLogger(__name__)

import os

from sqlalchemy import Column
from sqlalchemy.schema import Table, ForeignKey, FetchedValue
from sqlalchemy.types import Integer, Unicode, Float, Boolean, Date, DateTime
from sqlalchemy.orm import relationship, backref, joinedload, joinedload_all, contains_eager
from sqlalchemy.sql import and_, or_, not_, text
from sqlalchemy.sql.expression import func, case
from sqlalchemy import event

from zope.sqlalchemy import mark_changed

from . import Session
from ..utils.config import app_conf
from ..file_store.config import Original, Thumbnail
from ..render.template_helpers import subdomain


class ImageMixin(object):
    """
    Filesystem path: /<store-path>/images/<type>/<id>-<variant>.<ext>
    URL: <prefix>/<type>/<id>-<variant>.<ext>
    """

    id    = Column(Integer, primary_key=True)
    ext   = Column(Unicode)

    # override in entities
    type = ''
    variants = {
        '': Original()
    }

    # TODO make configurable!
    FS_PATH_PREFIX  = os.path.join(app_conf('store-path'), 'images')
    SRC_URL_PREFIX  = '//' + subdomain('static') + '/store/images/'

    def _get_filename(self, variant):
        if variant:
            variant = '-' + variant

        return u'%s%s.%s' % (self.id, variant, self.ext)

    def get_path(self, variant=''):
        """
        :return: absolute filesystem path to the image
        """
        return os.path.join(self.FS_PATH_PREFIX, self.type, self._get_filename(variant))

    def get_src(self, variant=''):
        """
        :return: URL suitable for use in <img src="">
        """
        return  self.SRC_URL_PREFIX + os.path.join(self.type, self._get_filename(variant))


# TODO http://docs.sqlalchemy.org/en/latest/orm/events.html
#      http://stackoverflow.com/questions/12023526/execute-some-code-when-an-sqlalchemy-objects-deletion-is-actually-committed
# @event.listens_for(ImageMixin, 'after_delete')
# def receive_after_delete(mapper, connection, target):
#     "listen for the 'after_delete' event"
#
#     # ... (event handling logic) ...
