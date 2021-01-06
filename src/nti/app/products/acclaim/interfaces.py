#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from nti.app.products.integration.interfaces import IIntegration

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.schema.field import ValidTextLine


class IAcclaimIntegration(IIntegration, ICreated, ILastModified):
    """
    Acclaim integration
    """

    authorization_token = ValidTextLine(title=u'Acclaim Integration',
                                        description=u"Acclaim integration",
                                        min_length=1)
