# coding: utf-8


def configure_template_globals(event):
    """
    BeforeRender subscriber
    pyramid defaults are request, context, renderer_name, renderer_info, view
    """

    event['c'] = event['request'].tmpl_context

    event['url'] = event['request'].route_url
    event['path'] = event['request'].route_path

    from . import template_helpers  # TODO
    event['h'] = template_helpers

    # TODO ??
    #from pyramid.security import authenticated_userid
    #event['user_id'] = authenticated_userid(event['request'])
