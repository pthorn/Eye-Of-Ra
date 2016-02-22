# coding: utf-8


def includeme(config):
    from pyramid.exceptions import NotFound, Forbidden, URLDecodeError
    from .views import (
        not_found, not_found_xhr,
        forbidden, forbidden_xhr,
        internal_error, url_decode_error)

    config.add_notfound_view(not_found, xhr=False)
    config.add_notfound_view(not_found_xhr, xhr=True)
    config.add_view(forbidden, context=Forbidden, xhr=False)
    config.add_view(forbidden_xhr, context=Forbidden, xhr=True)
    config.add_view(url_decode_error, context=URLDecodeError)
    #config.add_view(internal_error, context=Exception) # TODO
