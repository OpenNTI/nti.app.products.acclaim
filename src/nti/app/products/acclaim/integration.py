#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.app.products.acclaim.interfaces import IAcclaimIntegration

from nti.app.products.acclaim.model import AcclaimIntegration

from nti.app.products.integration.interfaces import IIntegrationCollectionProvider

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IIntegrationCollectionProvider)
class AcclaimIntegrationProvider(object):

    def can_integrate(self):
        #TODO: query site policy/license
        return True

    def get_collection_iter(self):
        """
        Return a AcclaimIntegration object by which we can enable
        Acclaim integration.
        """
        result = component.queryUtility(IAcclaimIntegration)
        if result is None:
            result = AcclaimIntegration(title=u'Integrate with Acclaim')
        return (result,)
