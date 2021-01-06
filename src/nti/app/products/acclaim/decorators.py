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

from zope.component.hooks import getSite

from zope.container.interfaces import ILocation

from nti.app.products.google.sso import ENABLE_ACCLAIM_VIEW

from nti.app.products.acclaim.interfaces import IAcclaimIntegration

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.app.products.acclaim.authorization import ACT_ACCLAIM

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.links import Link

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


def located_link(parent, link):
    interface.alsoProvides(link, ILocation)
    link.__name__ = ''
    link.__parent__ = parent
    return link


@component.adapter(IAcclaimIntegration)
@interface.implementer(IExternalMappingDecorator)
class _AcclaimEnableIntegrationDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, unused_result):
        current_site = getSite()
        return super(_AcclaimEnableIntegrationDecorator, self)._predicate(context, unused_result) \
           and has_permission(ACT_ACCLAIM, current_site, self.request) \
           and not context.authorization_token

    def _do_decorate_external(self, unused_context, result):
        links = result.setdefault(LINKS, [])
        link_context = getSite()
        link = Link(link_context,
                    elements=("@@" + ENABLE_ACCLAIM_VIEW,),
                    rel='enable')
        links.append(located_link(link_context, link))