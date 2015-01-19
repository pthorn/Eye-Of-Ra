# coding: utf-8

import email, smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm.exc import NoResultFound

from mako.template import Template
from mako.exceptions import MakoException

from .settings import app_conf


import logging
log = logging.getLogger(__name__)


class EmailException(Exception):
    pass


def send_email(to, subject, body, html=False):

    msg = MIMEText(body, 'html' if html else 'plain', 'utf-8')
    try:
        msg['From'] = app_conf('email-from')
        msg['To'] = to
        msg['Subject'] = subject
        smtp_host = app_conf('smtp-host')
    except KeyError as e:
        msg = 'ошибка в параметрах email: не указан параметр %s' % str(e)
        log.error(msg)
        raise EmailException(msg)

    try:
        s = smtplib.SMTP(smtp_host)
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
        log.info('отправлено сообщение %s, тема [%s]' % (to, subject))
    except Exception as e:
        msg = 'ошибка отправки сообщения на адрес %s, %s, smtp-host=%s' % (to, str(e), smtp_host)
        log.error(msg)
        raise EmailException(msg)


def send_auto_email(to, template_id, subst=None):

    def mako_subst(tpl, subst):
        try:
            return Template(tpl, default_filters=['h']).render_unicode(**subst)
        except MakoException as e:
            log.error('Mako exception: ' + str(e))
            raise EmailException('Mako exception: ' + str(e))

    from ..models import AutoEmailTemplate
    try:
        template = AutoEmailTemplate.get_by_id(template_id)
    except NoResultFound:
        msg = 'шаблон сообщения %s не найден' % template_id
        log.error(msg)
        raise EmailException(msg)
    if subst:
        template.expunge()
        template.subject = mako_subst(template.subject, subst)
        template.body = mako_subst(template.body, subst)
    send_email(to, template.subject, template.body, template.body_type == 'html')
