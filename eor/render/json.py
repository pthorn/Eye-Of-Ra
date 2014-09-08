# coding: utf-8

import datetime
import decimal

from pyramid.renderers import JSON


def configure_json_renderer(json):
    def datetime_adapter(obj, request):
        return obj.isoformat()

    def decimal_adapter(obj, request):
        return str(obj)

    json.add_adapter(datetime.datetime, datetime_adapter)
    json.add_adapter(decimal.Decimal, decimal_adapter)


def get_json_renderer(config):
    json = JSON()
    configure_json_renderer(json)
    return json
