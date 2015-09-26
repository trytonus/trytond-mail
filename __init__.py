# -*- coding: utf-8 -*-
"""
    __init__.py

"""
from trytond.pool import Pool

from mail import Mail


def register():
    Pool.register(
        Mail,
        module='mail', type_='model'
    )
