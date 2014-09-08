# coding: utf-8

import logging
log = logging.getLogger(__name__)

from pyramid.view import view_config
from pyramid.response import Response

from .captcha import Captcha


@view_config(route_name='captcha-image')
@view_config(route_name='captcha-image-w-formid')
def captcha(request):
    form_id = request.matchdict.get('form_id', u'')  # 2 routes: with and without form_id

    image, ctype = Captcha(request.client_addr, form_id).render()

    response = Response(body=image, content_type=ctype)
    response.content_length = len(image)
    response.cache_control = 'no-cache, no-store'

    return response
