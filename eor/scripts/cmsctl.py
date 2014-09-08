# coding: utf-8

import os
import sys

import pyramid.paster
import transaction

from eor.models import initialize_sqlalchemy, Session
from eor.utils import app_conf


def add_user(args):
    """
    """
    pass


def set_password_for_user(args):
    """
    """
    from eor.auth import settings as auth_settings
    auth_settings.user_model.set_new_password(password)


def exec_command():
    if command == 'set-password':
        pass


def main(argv=sys.argv):

    if len(argv) == 1:
        print('Usage: {0} ini.ini'.format(argv[0]))
        return 1

    pyramid.paster.setup_logging(argv[1])
    env = pyramid.paster.bootstrap(argv[1])
    settings = env['registry'].settings

    try:
        initialize_sqlalchemy(settings)

        with transaction.manager:
            exec_command()

    finally:

        env['closer']()


if __name__ == '__main__':
    main()
