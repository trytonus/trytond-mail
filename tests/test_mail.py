# -*- coding: utf-8 -*-
"""
    tests/test_mail.py

"""
import os
import unittest
from email.header import decode_header
if 'DB_NAME' not in os.environ:
    os.environ['TRYTOND_DATABASE_URI'] = 'sqlite://'
    os.environ['DB_NAME'] = ':memory:'

from stub import stub
import trytond.tests.test_tryton
from trytond.tests.test_tryton import (
    POOL, USER, DB_NAME, CONTEXT, ModuleTestCase
)
from trytond.transaction import Transaction


BASE_TEMPLATE = """\
|{% block block1 %}block 1 from base{% endblock %}
|{% block block2 %}block 2 from base{% endblock %}"""

INVITE_TEMPLATE = """\
|{% extends "mail/base.html" %}
|{% block block1 %}{{ message }}{% endblock %}"""

UNICODE_TEST_TEMPLATE = u"Somé unicøde testing"


def template_loader(name):
    """Patcher method for ``Mail.jinja_loader_func``.
    """
    if name == 'mail/base.html':
        return BASE_TEMPLATE
    elif name == "mail/invite.html":
        return INVITE_TEMPLATE
    elif name == "mail/unicode.html":
        return UNICODE_TEST_TEMPLATE


class TestMail(ModuleTestCase):

    module = 'mail'

    def setUp(self):
        trytond.tests.test_tryton.install_module('mail')

    def test_0005_render_email(self):
        """
        Render email
        """
        Mail = POOL.get('mail.mail')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            # Stubbing ``Mail.jinja_loader_func`` as it needs an actual
            # template from filesystem.
            stub(Mail.jinja_loader_func, template_loader)

            with self.assertRaises(Exception):
                # Try rendering mail without passing text
                # or html template
                Mail.render_email(
                    from_email="test@openlabs.co.in",
                    to='reciever@openlabs.co.in',
                    subject='Dummy subject of email',
                    cc=u'cc@openlabs.co.in'
                )

            email_message = Mail.render_email(
                from_email="test@openlabs.co.in",
                to='reciever@openlabs.co.in',
                subject='Dummy subject of email',
                text_template='mail/base.html',
                cc=u'cc@openlabs.co.in'
            )

            self.assertEqual(
                decode_header(email_message['From'])[0],
                ("test@openlabs.co.in", None)
            )

            self.assertEqual(
                decode_header(email_message['Subject'])[0],
                ('Dummy subject of email', None)
            )

            self.assertFalse(email_message.is_multipart())
            self.assertEqual(
                email_message.get_payload(decode=True),
                "|block 1 from base\n|block 2 from base",
            )

            # Email to can take comma separated email addresses.
            email_message = Mail.render_email(
                from_email="test@openlabs.co.in",
                to='reciever@openlabs.co.in, r2@openlabs.co.in',
                subject='Dummy subject of email',
                text_template='mail/base.html',
                cc=u'cc@openlabs.co.in'
            )
            self.assertEqual(
                decode_header(email_message['To'])[0],
                ('reciever@openlabs.co.in, r2@openlabs.co.in', None)
            )

    def test_0010_email_with_attachments(self):
        """
        Send an email with text, html and an attachment
        """
        Mail = POOL.get('mail.mail')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            # Stubbing ``Mail.jinja_loader_func`` as it needs an actual
            # template from filesystem.
            stub(Mail.jinja_loader_func, template_loader)

            email_message = Mail.render_email(
                from_email="test@openlabs.co.in",
                to='reciever@openlabs.co.in',
                subject='Dummy subject of email',
                text_template='mail/base.html',
                html_template='mail/base.html',
                attachments={'filename.pdf': 'some PDF content'},
            )

            self.assertEqual(
                decode_header(email_message['Subject'])[0],
                ('Dummy subject of email', None)
            )

            # Message type should be multipart/alternative
            self.assertTrue(email_message.is_multipart())
            self.assertEqual(
                email_message.get_content_type(), 'multipart/mixed'
            )

            # Ensure that there are two subparts
            self.assertEqual(
                len(email_message.get_payload()), 2
            )

            # Ensure that the subparts are 1 alternative and
            # octet-stream part
            payload_types = set([
                p.get_content_type() for p in email_message.get_payload()
            ])
            self.assertEqual(
                set(['multipart/alternative', 'application/octet-stream']),
                payload_types
            )

            # Drill into the alternative part and ensure that there is
            # both the text part and html part in it.
            for part in email_message.get_payload():
                if part.get_content_type() == 'multipart/alternative':
                    # Ensure that there are two subparts
                    # 1. text/plain
                    # 2. text/html
                    self.assertEqual(
                        len(email_message.get_payload()), 2
                    )
                    payload_types = set([
                        p.get_content_type()
                        for p in part.get_payload()
                    ])
                    self.assertEqual(
                        set(['text/plain', 'text/html']),
                        payload_types
                    )
                    break
            else:
                self.fail('Alternative part not found')

    def test_0015_email_inheritance(self):
        """
        Email inheritance is working!
        """
        Mail = POOL.get('mail.mail')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            # Stubbing ``Mail.jinja_loader_func`` as it needs an actual
            # template.
            stub(Mail.jinja_loader_func, template_loader)

            email_message = Mail.render_email(
                from_email="test@openlabs.co.in",
                to='reciever@openlabs.co.in',
                subject='Dummy subject of email',
                text_template='mail/invite.html',
                cc=u'cc@openlabs.co.in',
                message="testing"
            )

            self.assertFalse(email_message.is_multipart())
            self.assertEqual(
                email_message.get_payload(decode=True),
                "||testing\n|block 2 from base",
            )

    def test_0020_render_email_unicode(self):
        """
        Render email unicode
        """
        Mail = POOL.get('mail.mail')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            # Stubbing ``Mail.jinja_loader_func`` as it needs an actual
            # template from filesystem.
            stub(Mail.jinja_loader_func, template_loader)

            email_message = Mail.render_email(
                from_email=u"Soméøne <someone@email.com>",
                to=u'Søméone Else <someone.else@email.com> ',
                subject=u'Añ üñîçø∂é émåîl',
                text_template='mail/unicode.html',
                cc=u'cc@openlabs.co.in'
            )

            self.assertEqual(
                decode_header(email_message['From'])[0], (
                    u"Soméøne <someone@email.com>".encode('ISO-8859-1'),
                    'iso-8859-1'
                )
            )


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestMail),
    ])
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
