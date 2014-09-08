# coding: utf-8


def get_ip(request):
    """
    function for reified request property request.ip

    call at startup: config.add_request_method(get_ip, 'ip', reify=True)
    configure nginx: X-Forwarded-For $proxy_add_x_forwarded_for;
    """
    return request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.client_addr)) or 'unknown'
