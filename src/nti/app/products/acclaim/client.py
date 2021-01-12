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

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

from nti.app.products.acclaim import NT_EVIDENCE_NTIID_ID

from nti.app.products.acclaim.interfaces import IAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimClient
from nti.app.products.acclaim.interfaces import AcclaimClientError
from nti.app.products.acclaim.interfaces import IAcclaimIntegration
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimOrganization
from nti.app.products.acclaim.interfaces import IAcclaimBadgeCollection
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadgeCollection
from nti.app.products.acclaim.interfaces import IAcclaimOrganizationCollection
from nti.app.products.acclaim.interfaces import MissingAcclaimOrganizationError

from nti.dataserver.users.interfaces import IUserProfile
from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.ntiids.ntiids import is_valid_ntiid_string

logger = __import__('logging').getLogger(__name__)


@component.adapter(IAcclaimIntegration)
@interface.implementer(IAcclaimClient)
def integration_to_client(integration):
    if integration.authorization_token:
        return AcclaimClient(integration)


@interface.implementer(IAcclaimClient)
class AcclaimClient(object):
    """
    The client to interact with acclaim.
    """

    BASE_URL = 'https://api.youracclaim.com/v1'

    ORGANIZATIONS_URL = '/organizations'
    ORGANIZATIONS_ORG_URL = '/organizations/%s'
    ORGANIZATION_ALL_BADGES_URL = '/organizations/%s/badge_templates'
    ORGANIZATION_BADGE_URL = '/organizations/%s/badge_templates/%s'

    BADGE_URL = '/organizations/%s/badges'

    def __init__(self, integration):
        self.authorization_token = integration.authorization_token
        self.b64_token = b64encode(self.authorization_token)
        org_id = None
        if integration.organization:
            org_id = integration.organization.organization_id
        self.organization_id = org_id

    def _make_call(self, url, post_data=None, params=None, delete=False, acceptable_return_codes=None):
        if not acceptable_return_codes:
            acceptable_return_codes = (200,)
        url = '%s%s' % (self.BASE_URL, url)

        access_header = 'Bearer %s' % self.b64_token
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
        if sort:
            params['sort'] = sort
        if filters:
            params['filters'] = filters
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

    def _get_filter_str(self, filter_dict):
        result = ''
        for key, val in filter_dict.items():
            result += '%s::%s' % (key, val)
        return result

    def get_awarded_badges(self, user, sort=None, filters=None, page=None):
        """
        Return an :class:`IAwardedAcclaimBadgeCollection`.

        https://www.youracclaim.com/docs/issued_badges filtered by user email.
        """
        if not self.organization_id:
            raise MissingAcclaimOrganizationError()
        params = dict()
        filters = dict(filters) if filters else dict()
        filters['user_id'] = self._get_user_id(user)
        # Is this what we want?
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
        profile = IUserProfile(user)
        data = dict()
        data['user_id'] = self._get_user_id(user)
        # TODO: what email state is acceptable?
        # if invalid email, do we award badges after user updates email?
        data['recipient_email'] = profile.email

        # TODO: Raise if no real name?
        friendly_named = IFriendlyNamed(user)
        if friendly_named.realname and '@' not in friendly_named.realname:
            human_name = nameparser.HumanName(friendly_named.realname)
            data['issued_to_first_name'] = human_name.first
            data['issued_to_last_name'] = human_name.last
        data['badge_template_id'] = badge_template_id
        data['issued_at']
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

