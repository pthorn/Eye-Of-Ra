# coding: utf-8

class Config(object):

    def __init__(self):
        self.sqlalchemy_base_superclasses = None
        self.message_template = None
        self.forbidden_show_login_handler = None


config = Config()
