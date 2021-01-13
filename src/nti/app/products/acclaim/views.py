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

from nti.app.externalization.view_mixins import BatchingUtilsMixin
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.acclaim import ENABLE_ACCLAIM_VIEW
from nti.app.products.acclaim import ACCLAIM_INTEGRATION_NAME

from nti.app.products.acclaim import MessageFactory as _

from nti.app.products.acclaim.authorization import ACT_ACCLAIM

from nti.app.products.acclaim.interfaces import IAcclaimClient
from nti.app.products.acclaim.interfaces import IAcclaimIntegration

from nti.appserver.dataserver_pyramid_views import GenericGetView

from nti.appserver.ugd_edit_views import UGDPutView

from nti.dataserver.interfaces import IHostPolicyFolder

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.site.localutility import install_utility

from nti.site.utils import unregisterUtility

logger = __import__('logging').getLogger(__name__)

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
MIMETYPE = StandardExternalFields.MIMETYPE
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


def raise_error(data, tb=None,
                factory=hexc.HTTPUnprocessableEntity,
                request=None):
    raise_json_error(request, factory, data, tb)


class AcclaimIntegrationUpdateMixin(object):

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

    def _unregister_integration(self):
        registry = component.getSiteManager()
        unregisterUtility(registry, provided=IAcclaimIntegration)

    def _get_organizations(self, integration):
        client = IAcclaimClient(integration)
        return client.get_organizations()

    def set_organization(self, integration):
        organizations = self._get_organizations(integration)
        organizations = organizations.organizations
        if len(organizations) == 1:
            # Just one organization - set and use
            integration.organization = organizations[0]
            integration.organization.__parent__ = integration
            self._register_integration(integration)
        else:
            logger.warn("Multiple organizations tied to auth token (%s) (%s)",
                        integration.authorization_token,
                        organizations)
        return integration


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IHostPolicyFolder,
             request_method='POST',
             name=ENABLE_ACCLAIM_VIEW,
             permission=ACT_ACCLAIM)
class EnableAcclaimIntegrationView(AbstractAuthenticatedView,
                                   ModeledContentUploadRequestUtilsMixin,
                                   AcclaimIntegrationUpdateMixin):
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

    def _do_call(self):
        logger.info("Integration acclaim for site (%s) (%s)",
                    self.site.__name__, self.remoteUser)
        # XXX: The usual "what do we do" for parent and child site questions here.
        if component.queryUtility(IAcclaimIntegration):
            raise_error({'message': _(u"Acclaim integration already exist"),
                         'code': 'ExistingAcclaimIntegrationError'})
        integration = self.readCreateUpdateContentObject(self.remoteUser)
        if integration.organization:
            result = self._register_integration(integration)
        else:
            result = self.set_organization(integration)
        return result


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='PUT',
             permission=ACT_ACCLAIM,
             renderer='rest')
class AcclaimIntegrationPutView(UGDPutView,
                                AcclaimIntegrationUpdateMixin):

    def updateContentObject(self, obj, externalValue):
        super(AcclaimIntegrationPutView, self).updateContentObject(obj, externalValue)
        # If changing authorization token, refresh organization.
        if 'authorization_token' in externalValue:
            self.set_organization(obj)
        return obj


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='DELETE',
             permission=ACT_ACCLAIM,
             renderer='rest')
class AcclaimIntegrationDeleteView(AbstractAuthenticatedView,
                                   AcclaimIntegrationUpdateMixin):
    """
    Allow deleting (unauthorizing) a :class:`IWebinarAuthorizedIntegration`.
    """

    def __call__(self):
        self._unregister_integration()
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='GET',
             permission=ACT_ACCLAIM,
             name='organizations',
             renderer='rest')
class AcclaimIntegrationOrganizationsView(AbstractAuthenticatedView):

    def __call__(self):
        result = LocatedExternalDict()
        client = IAcclaimClient(self.context)
        organizations = client.get_organizations()
        result[ITEMS] = items = organizations
        result[ITEM_COUNT] = result[TOTAL] = len(items)
        return result


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='GET',
             permission=ACT_ACCLAIM,
             renderer='rest')
class AcclaimIntegrationGetView(GenericGetView):
    pass


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='GET',
             name='badges',
             permission=ACT_ACCLAIM,
             renderer='rest')
class AcclaimBadgesView(AbstractAuthenticatedView,
                        BatchingUtilsMixin):
    """
    Get all badges from this acclaim account

    TODO: Sorting, paging, filtering?
    """

    def __call__(self):
        client = IAcclaimClient(self.context)
        collection = client.get_badges(sort=None, filters=None, page=None)
        return collection
