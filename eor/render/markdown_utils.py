# coding: utf-8

from urllib.parse import urlparse

import markdown
from markdown.postprocessors import Postprocessor
from markdown import Extension

import bleach
from html5lib.sanitizer import HTMLSanitizer

from ..utils import app_conf


##
## linkify
##

class MyTokenizer(HTMLSanitizer):
    def sanitize_token(self, token):
        return token

class LinkifyPostprocessor(Postprocessor):
    """
    http://bleach.readthedocs.org/en/latest/linkify.html
    """

    @staticmethod
    def add_nofollow(attrs, new=False):
        our_domain_base = app_conf('main-domain-base')
        url = urlparse(attrs['href'])

        if not url.netloc.endswith(our_domain_base):
            attrs['rel'] = 'nofollow'
            attrs['class'] = 'external'

        return attrs

    def run(self, text):
        text = bleach.linkify(text, callbacks=[self.add_nofollow], tokenizer=MyTokenizer)
        return text

class LinkifyExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.postprocessors.add("linkify", LinkifyPostprocessor(md), "_begin")


##
## render_markdown()
##

ALLOWED_TAGS_BEFORE = bleach.ALLOWED_TAGS       #  as entered by user

def render_markdown(html):
    """
    http://pythonhosted.org/Markdown/reference.html
    http://bleach.readthedocs.org/en/latest/clean.html
    http://pyembed.github.io/usage/markdown/
    """

    html = bleach.clean(
        html,
        tags = ALLOWED_TAGS_BEFORE,
        # attributes=ALLOWED_ATTRIBUTES,
        # styles=ALLOWED_STYLES,
    )

    html = markdown.markdown(
        html,
        safe_mode = False,
        output_format = 'html5',
        extensions = [LinkifyExtension()]
    )

    return html
