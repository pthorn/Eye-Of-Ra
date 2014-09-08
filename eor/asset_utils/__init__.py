# coding: utf-8

def includeme(config):
    from ..utils import app_conf

    # TODO
    less_files = [
        dict(source=['eor/admin/static/style/style.css'], dest='victoria/admin/static/style/style-compiled.css'),
        dict(source=['eor/site/static/style/style.css'], dest='victoria/site/static/style/style-compiled.css')
    ]

    if app_conf('less') == 'static':
        pass
        #from .utils.less import compile_less
        #compile_less(less_files)
