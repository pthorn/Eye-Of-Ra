# coding: utf-8

from .pager import Pager
from .messages import render_message, add_flash_message
from .markdown_utils import render_markdown


def includeme(config):
    from .json import get_json_renderer
    config.add_renderer('json', get_json_renderer(config))

    from pyramid.events import BeforeRender
    from .template_config import configure_template_globals
    config.add_subscriber(configure_template_globals, BeforeRender)
