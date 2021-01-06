#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 124702 2017-12-08 21:11:48Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.container.contained import Contained

from nti.app.products.acclaim.interfaces import IAcclaimIntegration

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.representation import WithRepr

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@WithRepr
@interface.implementer(IAcclaimIntegration)
class AcclaimIntegration(SchemaConfigured,
                         PersistentCreatedModDateTrackingObject,
                         Contained):

    __parent__ = None
    __name__ = None

    createDirectFieldProperties(IAcclaimIntegration)
    mimeType = mime_type = "application/vnd.nextthought.site.acclaimintegration"
