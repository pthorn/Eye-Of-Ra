from nose.tools import *

from eor.utils import setting
from eor.utils.settings import (
    ParseSettings,
    SettingsParseException,
    UnknownSettingException,
    reset
)

    # (ParseSettings(settings, prefix='eor.')
    #     .string('mode', default='dev', variants=('dev', 'prod'))
    #     .path('store-path', default='../store')
    #     .string('domain')  # TODO in asset_utils?
    #     .string('static-domain'))

class TestSettings(object):

    @raises(UnknownSettingException)
    def test_nonexistent_setting(self):
        reset()
        setting('meow')


class TestParseSettings(object):

    @raises(SettingsParseException)
    def test_nonexistent(self):
        settings = {}

        reset()
        (ParseSettings(settings)
            .string('mode'))

    def test_prefix(self):
        settings = {
            'app.mode': 'prod',
            'eor.mode': 'meow'
        }

        reset()
        (ParseSettings(settings)
            .string('mode'))

        assert setting('app.mode') == 'prod'

    def test_variant_correct(self):
        settings = {'app.mode': 'prod'}

        reset()
        (ParseSettings(settings)
            .string('mode', default='dev', variants=('dev', 'prod')))

        assert setting('app.mode') == 'prod'

    @raises(SettingsParseException)
    def test_variant_bad(self):
        settings = {'app.mode': 'meow'}

        reset()
        (ParseSettings(settings)
            .string('mode', default='dev', variants=('dev', 'prod')))

    def test_bool(self):
        settings = {
            'app.a': 'true',
            'app.b': 'yes',
            'app.c': 'false',
            'app.d': 'no'
        }

        reset()
        (ParseSettings(settings)
            .bool('a')
            .bool('b')
            .bool('c')
            .bool('d'))

        assert setting('app.a') == True
        assert setting('app.b') == True
        assert setting('app.c') == False
        assert setting('app.d') == False
