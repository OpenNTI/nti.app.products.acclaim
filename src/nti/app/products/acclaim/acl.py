#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: acl.py 124926 2017-12-15 01:32:03Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from nti.app.products.acclaim.interfaces import IAcclaimIntegration

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.authorization import ROLE_ADMIN
from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.dataserver.interfaces import IACLProvider

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IACLProvider)
@component.adapter(IAcclaimIntegration)
class AcclaimIntegrationACLProvider(object):

    def __init__(self, context):
        self.context = context

    @property
    def __parent__(self):
        return self.context.__parent__

    @Lazy
    def __acl__(self):
        aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, type(self)),
                ace_allowing(ROLE_SITE_ADMIN, ALL_PERMISSIONS, type(self))]
        return acl_from_aces(aces)
