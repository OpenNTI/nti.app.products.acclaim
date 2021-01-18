#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import requests
import nameparser

from base64 import b64encode

from datetime import datetime

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from zope.intid.interfaces import IIntIds

from nti.app.products.acclaim import NT_EVIDENCE_NTIID_ID
from nti.app.products.acclaim import ACCLAIM_INTEGRATION_NAME

from nti.app.products.acclaim.interfaces import IAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimClient
from nti.app.products.acclaim.interfaces import AcclaimClientError
from nti.app.products.acclaim.interfaces import IAcclaimIntegration
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimOrganization
from nti.app.products.acclaim.interfaces import IAcclaimBadgeCollection
from nti.app.products.acclaim.interfaces import IAcclaimInitializationUtility
from nti.app.products.acclaim.interfaces import InvalidAcclaimIntegrationError
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadgeCollection
from nti.app.products.acclaim.interfaces import IAcclaimOrganizationCollection
from nti.app.products.acclaim.interfaces import MissingAcclaimOrganizationError

from nti.dataserver.users.interfaces import IUserProfile
from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.ntiids.ntiids import is_valid_ntiid_string

from nti.site.localutility import install_utility

logger = __import__('logging').getLogger(__name__)


@component.adapter(IAcclaimIntegration)
@interface.implementer(IAcclaimClient)
def integration_to_client(integration):
    if integration.authorization_token:
        return AcclaimClient(integration)


@interface.implementer(IAcclaimInitializationUtility)
class _AcclaimInitializationUtility(object):

    BASE_URLS = ('https://api.youracclaim.com/v1',
                 'https://sandbox.youracclaim.com/v1')

    @property
    def site(self):
        return getSite()

    @property
    def site_manager(self):
        return self.site.getSiteManager()

    def _register_integration(self, obj):
        obj.__name__ = ACCLAIM_INTEGRATION_NAME
        install_utility(obj,
                        utility_name=obj.__name__,
                        provided=IAcclaimIntegration,
                        local_site_manager=self.site_manager)
        return obj

    def _get_organizations(self, integration):
        client = IAcclaimClient(integration)
        return client.get_organizations()

    def set_organization(self, integration):
        """
        Fetch organizations, which should be a single entry.

        Raises :class:`InvalidAcclaimIntegrationError` if token is invalid.
        """
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

    def initialize(self, integration):
        """
        We have two possible API urls; try both. If successful, integration
        will have url and organization stored on it for future API calls.
        """
        invalid_exception = None
        for base_url in self.BASE_URLS:
            integration.base_url = base_url
            try:
                self.set_organization(integration)
            except InvalidAcclaimIntegrationError as exc:
                invalid_exception = exc
            else:
                return integration
        raise invalid_exception


@interface.implementer(IAcclaimClient)
class AcclaimClient(object):
    """
    The client to interact with acclaim.
    """

    ORGANIZATIONS_URL = '/organizations'
    ORGANIZATIONS_ORG_URL = '/organizations/%s'
    ORGANIZATION_ALL_BADGES_URL = '/organizations/%s/badge_templates'
    ORGANIZATION_BADGE_URL = '/organizations/%s/badge_templates/%s'

    BADGE_URL = '/organizations/%s/badges'

    def __init__(self, integration):
        self.authorization_token = integration.authorization_token
        # The authorization token is effectively the username; encode
        # with an empty password
        self.b64_token = b64encode('%s:' % self.authorization_token)
        org_id = None
        if integration.organization:
            org_id = integration.organization.organization_id
        self.organization_id = org_id
        self.base_url = integration.base_url

    def _make_call(self, url, post_data=None, params=None, delete=False, acceptable_return_codes=None):
        if not acceptable_return_codes:
            acceptable_return_codes = (200,)
        url = '%s%s' % (self.base_url, url)

        access_header = 'Basic %s' % self.b64_token
        if post_data:
            response = requests.post(url,
                                     json=post_data,
                                     headers={'Authorization': access_header,
                                              'Accept': 'application/json'})
        elif delete:
            response = requests.delete(url,
                                       headers={'Authorization': access_header})
        else:
            response = requests.get(url,
                                    params=params,
                                    headers={'Authorization': access_header})
        if response.status_code not in acceptable_return_codes:
            logger.warn('Error while making acclaim API call (%s) (%s) (%s)',
                        url,
                        response.status_code,
                        response.text)
            if response.status_code == 401:
                raise InvalidAcclaimIntegrationError(response.text)
            raise AcclaimClientError(response.text)
        return response

    def get_badge(self, badge_template_id):
        """
        Get the :class:`IAcclaimBadge` associated with the template id.
        """
        if not self.organization_id:
            raise MissingAcclaimOrganizationError()
        url = self.ORGANIZATION_BADGE_URL % (self.organization_id, badge_template_id)
        result = self._make_call(url)
        result = IAcclaimBadge(result.json())
        return result

    def get_badges(self, sort=None, filters=None, page=None):
        """
        Return an :class:`IAcclaimBadgeCollection`.

        https://www.youracclaim.com/docs/badge_templates
        """
        if not self.organization_id:
            raise MissingAcclaimOrganizationError()
        params = dict()
        filters = dict(filters) if filters else dict()
        filters['state'] = 'active'
        if sort:
            params['sort'] = sort
        if filters:
            params['filters'] = self._get_filter_str(filters)
        if page:
            params['page'] = page
        url = self.ORGANIZATION_ALL_BADGES_URL % self.organization_id
        result = self._make_call(url, params=params)
        result = IAcclaimBadgeCollection(result.json())
        return result

    def get_organization(self, organization_id):
        """
        Get the :class:`IAcclaimOrganization` for this organization id.
        """
        url = self.ORGANIZATIONS_ORG_URL % organization_id
        result = self._make_call(url)
        result = IAcclaimOrganization(result.json())
        return result

    def get_organizations(self):
        """
        Get all :class:`IAcclaimOrganization` objects.
        """
        url = self.ORGANIZATIONS_URL
        result = self._make_call(url)
        result = IAcclaimOrganizationCollection(result.json())
        return result

    def _get_user_id(self, user):
        intids = component.getUtility(IIntIds)
        return intids.getId(user)

    def _get_user_email(self, user):
        result = IUserProfile(user).email
        return result

    def _get_filter_str(self, filter_dict):
        result = ''
        for key, val in filter_dict.items():
            result += '%s::%s' % (key, val)
        return result

    def get_awarded_badges(self, user, sort=None, filters=None, page=None, public_only=None):
        """
        Return an :class:`IAwardedAcclaimBadgeCollection`.

        https://www.youracclaim.com/docs/issued_badges filtered by user email.
        """
        if not self.organization_id:
            raise MissingAcclaimOrganizationError()
        params = dict()
        filters = dict(filters) if filters else dict()
        # We want *all* badges tied to this user (by email) in Acclaim. The
        # user may have multiple email addresses on their Acclaim account.
        filters['recipient_email_all'] = self._get_user_email(user)
        if public_only:
            filters['public'] = True
        # We only want pending or accepted badges (not revoked or rejected)
        filters['state'] = 'pending,accepted'
        if sort:
            params['sort'] = sort
        if filters:
            params['filters'] = self._get_filter_str(filters)
        if page is not None:
            params['page'] = page
        url = self.BADGE_URL % self.organization_id
        result = self._make_call(url, params=params)
        result = IAwardedAcclaimBadgeCollection(result.json())
        return result

    def award_badge(self, user, badge_template_id, suppress_badge_notification_email=False, locale=None, evidence_ntiid=None):
        """
        Award a badge to a user.

        https://www.youracclaim.com/docs/issued_badges
        """
        if not self.organization_id:
            raise MissingAcclaimOrganizationError()
        data = dict()
        # We award this to our user's email address - no
        # matter if invalid, bounced etc.
        data['recipient_email'] = self._get_user_email(user)

        # TODO: Raise if no real name?
        friendly_named = IFriendlyNamed(user)
        if friendly_named.realname and '@' not in friendly_named.realname:
            human_name = nameparser.HumanName(friendly_named.realname)
            data['issued_to_first_name'] = human_name.first
            data['issued_to_last_name'] = human_name.last
        data['badge_template_id'] = badge_template_id
        data['issuer_earner_id'] = self._get_user_id(user)
        data['issued_at'] = datetime.utcnow().isoformat()
        data['suppress_badge_notification_email'] = suppress_badge_notification_email
        if locale:
            data['locale'] = locale
        if evidence_ntiid:
            assert is_valid_ntiid_string(evidence_ntiid)
            data['evidence'] = [{"type": "IdEvidence",
                                 "title": NT_EVIDENCE_NTIID_ID,
                                 "id": evidence_ntiid}]
        url = self.BADGE_URL % self.organization_id
        result = self._make_call(url, post_data=data)
        result = IAwardedAcclaimBadge(result.json())
        return result

