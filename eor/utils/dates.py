# coding: utf-8

"""
short time zone: import time; time.tzname[time.daylight]

long time zone:
    open('/etc/timezone').read().rstrip() (not all distros!)
    http://stackoverflow.com/questions/12521114/getting-the-canonical-time-zone-name-in-shell-script
    package tzlocal

pytz
    http://pytz.sourceforge.net/
    "This library differs from the documented Python API for tzinfo implementations"
    http://stackoverflow.com/questions/20500910/first-call-to-pytz-timezone-is-slow-in-virtualenv
    pip unzip pytz
"""

import logging
log = logging.getLogger(__name__)

import datetime
import pytz
from tzlocal import get_localzone

from pyramid.httpexceptions import HTTPNotModified


LOCAL = get_localzone()
UTC = pytz.timezone('UTC')


def localize(dt):
    return LOCAL.localize(dt)


def local_to_utc(dt):
    return UTC.normalize(localize(dt).astimezone(UTC))


def set_last_modified(request, last_modified):
    last_modified = local_to_utc(last_modified)

    if request.if_modified_since:
        if_modified_since = request.if_modified_since.replace(microsecond = 0)
        last_modified_cmp = last_modified.replace(microsecond = 0)
        if (if_modified_since - last_modified_cmp) >= datetime.timedelta(0):
            raise HTTPNotModified()

    request.response.last_modified = last_modified
