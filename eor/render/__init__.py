# coding: utf-8


# TODO!
class Settings(object):

    def __init__(self):
        self._message_template = None

    @property
    def message_template(self):
        if not self._message_template:
            raise RuntimeError("configuration parameter not present")
        return self._message_template

    @message_template.setter
    def message_template(self, val):
        self._message_template = val

settings = Settings()


from .messages import render_message, add_flash_message
from .markdown_utils import render_markdown


def includeme(config):
    from .json import get_json_renderer
    config.add_renderer('json', get_json_renderer(config))

    from pyramid.events import BeforeRender
    from .template_config import configure_template_globals
    config.add_subscriber(configure_template_globals, BeforeRender)


__all__ = [
    includeme,
    settings,
    render_message,
    add_flash_message
]
