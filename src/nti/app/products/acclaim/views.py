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

from nti.app.products.acclaim import BADGES
from nti.app.products.acclaim import ENABLE_ACCLAIM_VIEW

from nti.app.products.acclaim import MessageFactory as _

from nti.app.products.acclaim.authorization import ACT_ACCLAIM

from nti.app.products.acclaim.interfaces import IAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimClient
from nti.app.products.acclaim.interfaces import AcclaimClientError
from nti.app.products.acclaim.interfaces import IAcclaimIntegration
from nti.app.products.acclaim.interfaces import IAcclaimInitializationUtility
from nti.app.products.acclaim.interfaces import InvalidAcclaimIntegrationError

from nti.appserver.dataserver_pyramid_views import GenericGetView

from nti.appserver.ugd_edit_views import UGDPutView
from nti.appserver.ugd_edit_views import UGDDeleteView

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IHostPolicyFolder

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

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

    def _unregister_integration(self):
        registry = component.getSiteManager()
        unregisterUtility(registry, provided=IAcclaimIntegration)

    def set_organization(self, integration):
        """
        Fetch organizations, which should be a single entry. This should be
        called every time the authorization token is updated.

        Raises :class:`InvalidAcclaimIntegrationError` if token is invalid.
        """
        intialization_utility = component.getUtility(IAcclaimInitializationUtility)
        try:
            intialization_utility.initialize(integration)
        except InvalidAcclaimIntegrationError:
            raise_error({'message': _(u"Invalid Acclaim authorization_token."),
                         'code': 'InvalidAcclaimAuthorizationTokenError'})
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
    Allow deleting (unauthorizing) a :class:`IAcclaimIntegration`.
    """

    def __call__(self):
        try:
            del self.site_manager[self.context.__name__]
        except KeyError:
            pass
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
        try:
            organizations = client.get_organizations()
        except AcclaimClientError:
                raise_error({'message': _(u"Error during integration."),
                             'code': 'AcclaimClientError'})
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
             context=IAcclaimBadge,
             request_method='DELETE',
             permission=ACT_ACCLAIM,
             renderer='rest')
class AcclaimBadgeDeleteView(UGDDeleteView):
    """
    Allow deleting a :class:`IAcclaimBadge`.
    """

    def __call__(self):
        try:
            del self.context.__parent__[self.context.__name__]
        except KeyError:
            pass
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             context=IAcclaimIntegration,
             request_method='GET',
             name=BADGES,
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
        try:
            collection = client.get_badges(sort=None, filters=None, page=None)
        except AcclaimClientError:
                raise_error({'message': _(u"Error while getting badge templates."),
                             'code': 'AcclaimClientError'})
        return collection


@view_config(route_name='objects.generic.traversal',
             context=IUser,
             request_method='GET',
             name=BADGES,
             permission=ACT_READ,
             renderer='rest')
class UserAwardedBadgesView(AbstractAuthenticatedView,
                            BatchingUtilsMixin):
    """
    Get all awarded badges for this user.

    Other parties will only be able to see public badges.

    TODO: Sorting, paging, filtering?
    """

    def __call__(self):
        public_only = self.remoteUser != self.context
        integration = component.queryUtility(IAcclaimIntegration)
        if not integration:
            raise hexc.HTTPNotFound()
        client = IAcclaimClient(integration)
        try:
            collection = client.get_awarded_badges(self.context,
                                                   sort=None,
                                                   filters=None,
                                                   page=None,
                                                   public_only=public_only)
        except AcclaimClientError:
                raise_error({'message': _(u"Error while getting issued badges."),
                             'code': 'AcclaimClientError'})
        return collection
