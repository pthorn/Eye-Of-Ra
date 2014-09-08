# coding: utf-8

import datetime

import logging
log = logging.getLogger(__name__)

import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

import colander

from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from .. import models
from ..utils import app_conf
from ..auth import ebff


#@view_defaults(renderer='json')
class RestViews(object):

    def __init__(self, request):
        self.request = request
        self.delegate = RestDelegate()  # TODO

    def _error(self):
        """
        return a JSON response with error information
        """
        pass

    #@view_config()
    def get_list(self):
        """
        GET /prefix/{entity}[?qs]
        parameters:
        """
        pass

    #@view_config()
    def get_by_id(self):
        """
        GET /prefix/{entity}/{id}
        """
        pass

    #@view_config()
    def create(self):
        """
        PUT /prefix/{entity}/{id}
        """
        pass

    #@view_config()
    def update(self):
        """
        POST /prefix/{entity}/{id}
        """
        pass

    #@view_config()
    def delete(self):
        """
        DELETE /prefix/{entity}/{id}
        """
        pass

    #@view_config()
    def custom(self):
        """
        POST /prefix/{entity}/{id}/{method}
        """
        pass


class RestDelegate(object):

    def __init__(self):
        self.name = None  # 'entity' -> /rest/entities, /rest/entity/{id} etc.
        self.entity = None # models.Entity

        # entity methods
        self.entity_getter      = 'get_by_id'
        self.entity_list_getter = 'get_list_for_rest'  # TODO RestMixin?

        self.only_fields = None
        self.additional_fields = None

        self.schema = None # self.schema() should return colander schema

    def get_entity(self):
        return self.entity

    def get_schema(self):
        return self.schema

    def get_obj_list(self):
        return entity.get_for_rest_list(TODO) # TODO

    def get_obj_by_id(self):
        return entity.get_by_id(todo) # TODO

    def get_fields_for_list(self):
        pass # TODO

    def create_obj(self):
        return self.entity()

    def after_create_obj(self, obj, appstruct):
        pass

    def before_update_obj(self):
        pass # TODO

    def after_update_obj(self, obj, appstruct):
        pass

    def before_delete(self):
        return True

    def after_delete(self):
        pass



# TODO configure views: permission etc.

class Rest(object):
    """
    """

    def __init__(self, request=None):
        """
        """
        self.name = None  # 'entity' -> /rest/entities, /rest/entity/{id} etc.
        self.entity = None # models.Entity

        # entity methods
        self.entity_getter      = 'get_by_id'
        self.entity_list_getter = 'get_list_for_rest'  # TODO RestMixin?

        self.only_fields = None
        self.additional_fields = None

        self.schema = None # self.schema() should return colander schema

        ####

        self.request = request

    def register_method(self, method, url_part):
        pass

    def configure(self, config):
        """
        FooRest().configure(config)
        """
        pass

    def get_list(self):
        pass

    def get_by_id(self):
        pass

    def create(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

    def after_create(self, obj, appstruct):
        pass


#####################################################

class Test(Rest):

    def __init__(self, request=None):
        super(Test, self).__init__(request)

        self.name = 'test'
        self.entity = models.Base # some entity

        self.register_method('approve')

    def approve(self):
        try:
            approve = self.request.json_body['approve']
        except KeyError:
            raise RestError() # TODO! returns {status: 'error', ...}

#####################################################


# TODO colander field for xxx
class M2MField(object):
    pass
