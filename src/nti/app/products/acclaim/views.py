#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from zope import component

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.acclaim import ENABLE_ACCLAIM_VIEW
from nti.app.products.acclaim import ACCLAIM_INTEGRATION_NAME

from nti.app.products.acclaim import MessageFactory as _

from nti.app.products.acclaim.authorization import ACT_ACCLAIM

from nti.app.products.acclaim.interfaces import IAcclaimIntegration

from nti.appserver.dataserver_pyramid_views import GenericGetView

from nti.appserver.ugd_edit_views import UGDPutView

from nti.dataserver.interfaces import IHostPolicyFolder

from nti.externalization.interfaces import StandardExternalFields

from nti.site.localutility import install_utility

logger = __import__('logging').getLogger(__name__)

MIMETYPE = StandardExternalFields.MIMETYPE


def raise_error(data, tb=None,
                factory=hexc.HTTPUnprocessableEntity,
                request=None):
    raise_json_error(request, factory, data, tb)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IHostPolicyFolder,
             request_method='POST',
             name=ENABLE_ACCLAIM_VIEW,
             permission=ACT_ACCLAIM)
class EnableAcclaimIntegrationView(AbstractAuthenticatedView,
                                   ModeledContentUploadRequestUtilsMixin):
    """
    Enable the acclaim integration
    """

    DEFAULT_FACTORY_MIMETYPE = "application/vnd.nextthought.site.acclaimintegration"

    def readInput(self, value=None):
        if self.request.body:
            values = super(EnableAcclaimIntegrationView, self).readInput(value)
        else:
            values = self.request.params
        values = dict(values)
        # Can't be CaseInsensitive with internalization
        if MIMETYPE not in values:
            values[MIMETYPE] = self.DEFAULT_FACTORY_MIMETYPE
        return values

    @Lazy
    def site(self):
        return getSite()

    @Lazy
    def site_manager(self):
        return self.site.getSiteManager()

    def _register_integration(self, obj):
        obj.__name__ = ACCLAIM_INTEGRATION_NAME
        install_utility(obj,
                        utility_name=obj.__name__,
                        provided=IAcclaimIntegration,
                        local_site_manager=self.site_manager)
        return obj

    def _do_call(self):
        logger.info("Integration acclaim for site (%s) (%s)",
                    self.site.__name__, self.remoteUser)
        if component.queryUtility(IAcclaimIntegration):
            raise_error({'message': _(u"Acclaim integration already exist"),
                         'code': 'ExistingAcclaimIntegrationError'})
        integration = self.readCreateUpdateContentObject(self.remoteUser)
        self._register_integration(integration)
        return integration


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='PUT',
             permission=ACT_ACCLAIM,
             renderer='rest')
class AcclaimIntegrationPutView(UGDPutView):
    pass


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='GET',
             permission=ACT_ACCLAIM,
             renderer='rest')
class AcclaimIntegrationGetView(GenericGetView):
    pass
