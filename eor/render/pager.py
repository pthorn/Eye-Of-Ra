# coding: utf-8

import logging
log = logging.getLogger(__name__)

import copy

from sqlalchemy import desc
from sqlalchemy.exc import ProgrammingError

from pyramid.httpexceptions import HTTPNotFound


class Pager(list):
    """
    in view callable:
        c.items = Pager(request, session.query(models.Model)..., items_per_page=20, ...)
    in template:
        ${c.items.column_link('column')}
        ${c.items.pager(pager_class='pager', ...)}

    if several pagers are used on the same page, make sure that you specify different page/order parameters for each

    TODO
        - how do joined queries behave?
        - sort indicators for column links? need to return <a> instead of just url then
        - default sort
        - prefix for all parameters?
    """

    def __init__(self,
                request,
                sa_query,
                prefix = '',
                items_per_page = 20,
                page_param = 'page',
                order_param = 'order',
                initial_page = None):
        """
        pager = Pager(request, sqlalchemy_query, items_per_page=20, page_param='page', order_param='order')
        """

        self.request = request
        self.sa_query = sa_query
        self.items_per_page = items_per_page
        self.page_param = prefix + page_param
        self.order_param = prefix + order_param
        self.item_count = sa_query.count() # does select count() from sa_query
        self.last_page_no = (self.item_count - 1) // self.items_per_page + 1

        if self.item_count == 0:
            list.__init__(self, [])
            return

        if initial_page:
            self.current_page_no = initial_page
        else:
            try:
                self.current_page_no = int(request.matchdict.get(self.page_param, request.params.get(self.page_param, 1)))
            except ValueError:
                self.current_page_no = 1
        if self.current_page_no < 1:
            self.current_page_no = 1
        if self.current_page_no > self.last_page_no:
            self.current_page_no = self.last_page_no

        order = request.matchdict.get(self.order_param, request.params.get(self.order_param, None))
        if order:
            self.order_field = order.lstrip('-')
            self.order_is_desc = order.startswith('-')
            # TODO joined queries?!
            if hasattr(sa_query.column_descriptions[0]['type'], self.order_field):
                sa_query = sa_query.order_by(desc(self.order_field) if self.order_is_desc else self.order_field)
            else:
                log.warn('Pager: order by unknown field "%s", url: %s' % (self.order_field, self.request.url))
        else:
            self.order_field = None
            self.order_is_desc = False

        try:
            list.__init__(self, sa_query[(self.current_page_no-1)*self.items_per_page : self.current_page_no*self.items_per_page]) # select *  from sa_query
        except ProgrammingError:  # bad order field causes this TODO remove?
            raise HTTPNotFound()

    def pager(self,
              pager_class = 'pager',
              link_class = 'pager-link',
              cur_link_class = 'current',
              render_current_link_as_a = False,
              dots_class = 'dots',
              n_of_neigbours = 3):
        """
        render html for pager (for use in templates)
        usage (mako):
            ${c.items.pager(pager_class='my-pager', ...) | n}
        arguments:
            n_of_neigbours           - number of page links on both sides of the current page, default is 3 (n-3, n-2, n-1, n, n+1, n+2, n+3)
            pager_class              - css class for the pager div
            link_class               - css class for the link
            cur_link_class           - css class for current link (<a> or <span> depending on the next parameter)
            render_current_link_as_a - if True, render link to current page as <a>, otherwise (default) render as <span>
            dots_class               - css class for dots (wrapped in <span>)
        """

        def page_link(page_no):

            if page_no == self.current_page_no and not render_current_link_as_a:
                return '<span class="%s">%s</span>' % (cur_link_class, page_no)

            if page_no == 1:
                url = route_to_self(self.request, delete=[self.page_param])
            else:
                url = route_to_self(self.request, set={self.page_param: page_no})

            return '<a href="%(url)s" class="%(link_class)s">%(text)s</a>' % dict(
                url = url,
                text = page_no,
                link_class = cur_link_class if page_no == self.current_page_no else link_class
            )

        if self.item_count <= self.items_per_page:
            return ''

        result = page_link(1)
        if self.current_page_no - n_of_neigbours > 2:
            result += '<span class="%s">...</span> ' % dots_class
        for n in range(max(2, self.current_page_no-n_of_neigbours), min(self.current_page_no+n_of_neigbours, self.last_page_no)+1):
            result += page_link(n)
        if self.current_page_no + n_of_neigbours + 1 < self.last_page_no:
            result += '<span class="%s">...</span> ' % dots_class
        if self.current_page_no + n_of_neigbours < self.last_page_no:
            result += page_link(self.last_page_no)

        print(vars())

        if self.last_page_no > n_of_neigbours:
            result += '\n<form action="" method="GET"><select name="page" onChange="this.form.submit();">' + \
                ''.join(['<option value="%(n)s"%(sel)s>%(n)s</option>' % dict(n=n, sel=' selected="selected"' if n == self.current_page_no else '') for n in range(1, self.last_page_no+1)])\
                + '</select></form>'

        return '<div class="%s">\n%s\n</div>'  % (pager_class, result)

    def column_link(self, field):
        """
        returns a link for a column header to order by that column
        field - sqlalchemy field
        """

        order_is_desc = not self.order_is_desc if field == self.order_field else False
        order_param_val = ('-' if order_is_desc else '') + field

        return route_to_self(self.request, set={self.order_param: order_param_val}, delete=[self.page_param])


def route_to_self(request, set=dict(), delete=[]):
    """
    returns a route to the current page with current request parameters preserved, except:
        delete parameters present in 'delete' (sequence)
        set parameters in 'set' (dictionary)
    """

    query_params = {p:v for p, v in request.params.items() if p not in delete}
    query_params.update(set)

    route_path_args = copy.copy(request.matchdict) # so that route_path can fill route varilables
    if len(query_params): route_path_args['_query'] = query_params # http://docs.pylonsproject.org/projects/pyramid/dev/api/url.html#pyramid.url.route_url

    return request.route_path(request.matched_route.name, **route_path_args)
