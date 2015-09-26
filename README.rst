Trytond Mail
=============

.. image:: https://secure.travis-ci.org/fulfilio/trytond-mail.png?branch=develop
  :target: https://travis-ci.org/fulfilio/trytond-mail

One does not simply send emails!
--------------------------------

Sending emails from tryton modules is a frequent requirement. This module
makes it easier by providing a convenient and consistent API to generate email
messages. In addition, the module gives you a few goodies (template
inheritance, filters) that come in handy when sending emails.

Installation
------------

The module can be installed from pypi

.. code-block:: sh

    pip install fio_mail

.. tip::

   Remember to install a version compatible with your version of trytond.

Alternatively the module could be added as a dependency to your module

.. code-block:: python

    # your_module/tryton.cfg
    [tryton]
    ...
    depends:
      ...
      mail
      ...

See `sale-confirmation-email module <https://github.com/fulfilio/trytond-sale-confirmation-email/blob/01e0887bfa96044318b0bf7b43094b3ee4a1e2fb/tryton.cfg#L6>`_
for practical example.

If you use setup.py to install modules, remember to set the prefix as
fio for the modules. The `setup.py file <https://github.com/fulfilio/trytond-sale-confirmation-email/blob/01e0887bfa96044318b0bf7b43094b3ee4a1e2fb/setup.py#L94>`_ 
from `sale confirmation email module <https://github.com/fulfilio/trytond-sale-confirmation-email>`_ 
is a good example.

Quickstart
----------

Here is a code example, if you wished to send emails when sale orders are
confirmed

.. code-block:: python

    def confirm(cls, sales):
        Mail = Pool().get('mail.mail')

        # Call super function to confirm
        super(Sale, cls).confirm(sales)

        # Send an email for each order
        for sale in sales:
            email_message = Mail.render_email(
                from_email='order-confirmation@mydomain.com',
                to=[sale.party.email],
                subject='Your Order is confirmed',
                text_template='my_module/emails/order-confirmed.txt',
                sale=self,      # passed to template context
            )
            # send email_message using your preferred gateway

Detailed Introduction
---------------------

The module provides a convenient method named ``render_email`` which returns
a python ``mail.Message`` object which can then be sent using smtpservers.

.. tip::

   Sending emails during a transaction could be slow and result in bad
   user experience. Use the 
   `email-queue <https://github.com/fulfilio/email-queue>`_ module instead.


Rendering of templates
``````````````````````

The email requires at-least one of either ``html`` or ``text`` templates to be
specified. Specifying both is recommended as some email clients prefer to
display text content when available.

Specifying both text and html parts

.. code-block:: python

    email_message = Mail.render_email(
        from_email='me@mydomain.com',
        to=['you@somewhere.com'],
        subject='A great honking email',
        text_template='my_module/emails/honking-email.txt',
        html_template='my_module/emails/honking-email.html',
    )

The template name is expected to be in the format:
`<module_name>/path/to/email/template`.

.. tip::

   Remember to add the folder containing email templates to your data in
   `setup.py` to ensure they are copied to site-packages and distributed
   with your module.

Extending templates (DRY)
`````````````````````````

Every business is unique and so should be their emails. You may want to
add content to your template, change the design or completely overwrite
the email. If your goal is to add (extend) the email, the API allows you
to do it without repeating yourself.

In your downstream module, extend the template

.. code-block:: html+jinja

    {% extends 'sale-confirmation-email/email//sale-confirmation-html.html' %}

    {% block footer %}
    {{ super() }}
    <br/>
    Visit us on <a href="https://facebook.com/mybusiness">facebook</a>
    {% endblock footer %}

In the above example, the standard template bundled with the 
`sale confirmation email module <https://github.com/fulfilio/trytond-sale-confirmation-email>`_ 
is extended to add a link to the facebook page.

This pattern is common if you are familiar with the 
`jinja2 <http://jinja.pocoo.org/>`_ templating engine. You can learn more 
about extending them from `jinja2 docs <http://jinja.pocoo.org/docs/dev/templates/#template-inheritance>`_


Template Filters
````````````````

Variable within templates can be modified using filters

``{{ name|striptags|title }}`` for example will remove all HTML Tags from the
name and title-cases it. Filters that accept arguments have parentheses around
the arguments, like a function call. This example will join a list by commas: 
``{{ list|join(', ') }}``.

The `List of Builtin Filters <http://jinja.pocoo.org/docs/dev/templates/#list-of-builtin-filters>`_ 
on Jinja2 documentation describes all the builtin filters. In addition,
this module offers the following filters:

dateformat(date, format='medium')
+++++++++++++++++++++++++++++++++

Format the date with the current language from the context. For other
possible formats, refer the 
`babel documentation <http://babel.pocoo.org/docs/dates/#date-and-time>`_.

Example

.. code-block:: html+jinja

    <td>Date</td>
    <td>{{ sale.date|dateformat }}</td>

datetimeformat(datetime, format)
++++++++++++++++++++++++++++++++

Format the datetime with the current language from the context. For other
possible formats, refer the 
`babel documentation <http://babel.pocoo.org/docs/dates/#date-and-time>`_.

Example

.. code-block:: html+jinja

    Created on {{ sale.create_date|datetimeformat('long') }}</td>

currencyformat(amount, currency, format=None)
+++++++++++++++++++++++++++++++++++++++++++++

Return formatted currency value. For more formatting information refer
`babel documentation <http://babel.pocoo.org/docs/api/numbers/?highlight=format_currency#babel.numbers.format_currency>`_

Example

.. code-block:: html+jinja

    <td>Total Value</td>
    <td>{{ sale.total_amount|currencyformat(sale.currency.code) }}</td>


to, cc and bcc
```````````````

Sending an email to a certain set of recepients is different from setting
the recepient headers on the email. To indicate the recepients, send a
list of recepients to the ``to`` argument.

While ``cc`` is a commonly set header to indicate the recepients who have been 
copied the email, setting ``bcc`` would defeat the purpose as the recepients 
would be disclosed to everyone. Hence ``cc`` is the only other argument
accepted by the ``render_email`` method. To send a ``bcc``, you could send the
same message to the recepient when using the smtpserver to send email.

Example

.. code-block:: python

    email_message = Mail.render_email(
        to=['you@somewhere.com', 'youtoo@somewhere.com'],
        cc=['myself@mydomain.com'],

        # Usual stuff
        from_email='me@mydomain.com',
        subject='A great honking email',
        text_template='my_module/emails/honking-email.txt',
    )
    

Sending attachments
```````````````````

The method also accepts an argument ``attachments`` which takes a dictionary
where keys represent the filenames and the values are buffer streams of
the content to be attached. If attachment(s) are present, the mail type is
automatically changed to ``multipart/mixed``. The attachments should appear
as downloadable attachments on email clients

Example of sending

.. code-block:: python

    # Read a file from filesystem
    order_copy = buffer(open('order_copy.pdf').read())

    # From a binary field in tryton
    product_photo = product.image

    email_message = Mail.render_email(
        attachments={
            'order-copy.pdf': order_copy,
            'product-photo.png': product_photo,
        },

        # Other usual stuff
        from_email='me@mydomain.com',
        to=['you@somewhere.com'],
        subject='A great honking email',
        text_template='my_module/emails/honking-email.txt',
        html_template='my_module/emails/honking-email.html',
    )

Authors and Contributors
------------------------

This module was built at `Fulfil.IO <http://www.fulfil.io>`_. 

Professional Support
--------------------

This module is professionally supported by `Fulfil.IO <http://www.fulfil.io>`_.
If you are looking for on-site teaching or consulting support, contact our
`sales <mailto:sales@fulfil.io>`_ and `support
<mailto:support@fulfil.io>`_ teams.
