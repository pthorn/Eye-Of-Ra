# coding: utf-8

import markupsafe

from eor_settings import get_setting
from ..asset_utils import webpack_asset


def static_domain():
    return get_setting('eor.static-domain')


def css_class(**kwargs):
    """ <div ${h.css_class(foo_bar=True, meow=False) | n}> -> <div class="foo-bar"> """
    classes = ' '.join([k.replace('_', '-') for k, v in kwargs.iteritems() if v])
    return u'class="%s"' % markupsafe.escape(classes) if classes else u''


def static_serial():
    """
    .ini: app.static-serial = 1
    <script src="/site/js/site.js${h.static_serial() | n}"></script>
    """
    serial = get_setting('eor.static-serial')
    return u'?%s' % serial if serial else u''


def group(lst, group):
    """
    group([1,2,3,4,5,6,7,8], 3) -> [[1, 2, 3], [4, 5, 6], [7, 8]]
    """
    add_1 = 0 if len(lst) % group == 0 else 1
    return [lst[i*group:(i+1)*group] for i in range(len(lst)/group+add_1)]


def plural(n, zero, one, few, many):
    if n == 0 and zero:
        return zero

    rem = n % 10

    if rem == 1 and n != 11:
        return one
    elif rem in (2, 3, 4) and (n < 10 or n > 20):
        return few
    else:
        return many
