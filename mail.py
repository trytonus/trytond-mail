# -*- coding: utf-8 -*-
"""
    mail.py

"""
import os
from functools import partial
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase
from email.header import Header
from email import Encoders
from email.Utils import formatdate

from jinja2 import Environment, FunctionLoader, Template
from babel.dates import format_date, format_datetime
from babel.numbers import format_currency
from trytond.model import ModelView
from trytond.tools import file_open
from trytond.transaction import Transaction


class Mail(ModelView):
    "Trytond Mail Helper Class"
    __name__ = "mail.mail"

    @classmethod
    def jinja_loader_func(cls, name):  # pragma: no cover
        """
        Return the template from the module directories using the logic
        below:
        The name is expected to be in the format:
            <module_name>/path/to/email/template
        for example, if the party module had a base email template in
        its emails folder, then you should be able to use:
            {% extends 'party/emails/base.html' %}
        """
        module, path = name.split('/', 1)
        try:
            return file_open(os.path.join(module, path)).read()
        except IOError:
            return None

    @classmethod
    def get_jinja_filters(cls):
        """
        Returns filters that are made available in the template context.
        By default, the following filters are available:
        * dateformat: Formats a date using babel
        * datetimeformat: Formats a datetime using babel
        * currencyformat: Formats the given number as currency
        For additional arguments that can be passed to these filters,
        refer to the Babel `Documentation
        <http://babel.edgewall.org/wiki/Documentation>`_.
        """
        return {
            'dateformat': partial(format_date, locale=Transaction().language),
            'datetimeformat': partial(
                format_datetime, locale=Transaction().language
            ),
            'currencyformat': partial(
                format_currency, locale=Transaction().language
            ),
        }

    @classmethod
    def render_template(cls, template_string, **context):
        """
        Render the template using Jinja2
        """
        env = Environment(loader=FunctionLoader(cls.jinja_loader_func))
        env.filters.update(cls.get_jinja_filters())
        template = env.get_template(template_string)
        return template.render(**context)

    @classmethod
    def render_email(
        cls, from_email, to, subject, text_template=None, html_template=None,
        cc=None, attachments=None, **context
    ):
        """
        Read the templates for email messages, format them, construct
        the email from them and return the corresponding email message
        object.
        :param from_email: Email From
        :param to: Email IDs of direct recepients
        :param subject: Email subject
        :param text_template: <Text email template path>
        :param html_template: <HTML email template path>
        :param cc: Email IDs of Cc recepients
        :param attachments: A dict of filename:string as key value pair
                            [preferable file buffer streams]
        :param context: Context to be sent to template rendering
        :return: Email multipart instance or Text/HTML part
        """
        if not (text_template or html_template):
            raise Exception("Atleast HTML or TEXT template is required")

        text_part = None
        if text_template:
            if isinstance(text_template, Template):
                text = text_template.render(**context)
            else:
                text = unicode(cls.render_template(text_template, **context))
            text_part = MIMEText(
                text.encode("utf-8"), 'plain', _charset="UTF-8"
            )

        html_part = None
        if html_template:
            if isinstance(html_template, Template):
                html = html_template.render(**context)
            else:
                html = unicode(cls.render_template(html_template, **context))
            html_part = MIMEText(html.encode("utf-8"), 'html', _charset="UTF-8")

        if text_part and html_part:
            # Construct an alternative part since both the HTML and Text Parts
            # exist.
            message = MIMEMultipart('alternative')
            message.attach(text_part)
            message.attach(html_part)
        else:
            # only one part exists, so use that as the message body.
            message = text_part or html_part

        if attachments:
            # If an attachment exists, the MimeType should be mixed and the
            # message body should just be another part of it.
            message_with_attachments = MIMEMultipart('mixed')

            # Set the message body as the first part
            message_with_attachments.attach(message)

            # Now the message _with_attachments itself becomes the message
            message = message_with_attachments

            for filename, content in attachments.items():
                part = MIMEBase('application', "octet-stream")
                part.set_payload(content)
                Encoders.encode_base64(part)
                # XXX: Filename might have to be encoded with utf-8,
                # i.e., part's encoding or with email's encoding
                part.add_header(
                    'Content-Disposition',
                    'attachment; filename="%s"' % filename
                )
                message.attach(part)

        if isinstance(to, (list, tuple)):
            to = ', '.join(to)

        # We need to use Header objects here instead of just assigning the
        # strings in order to get our headers properly encoded (with QP).
        message['Subject'] = Header(unicode(subject), 'ISO-8859-1')
        message['From'] = Header(unicode(from_email), 'ISO-8859-1')
        message['To'] = Header(unicode(to), 'ISO-8859-1')
        message['Date'] = Header(unicode(formatdate()), 'ISO-8859-1')
        if cc:
            message['Cc'] = Header(unicode(cc), 'ISO-8859-1')

        return message
