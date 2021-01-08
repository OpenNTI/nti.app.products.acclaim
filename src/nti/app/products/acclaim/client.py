#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import requests

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from nti.app.products.acclaim.interfaces import IAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimClient
from nti.app.products.acclaim.interfaces import AcclaimClientError
from nti.app.products.acclaim.interfaces import IAcclaimIntegration
from nti.app.products.acclaim.interfaces import IAcclaimBadgeCollection

logger = __import__('logging').getLogger(__name__)


@component.adapter(IGoToWebinarAuthorizedIntegration)
@interface.implementer(IWebinarClient)
class GoToWebinarClient(object):
    """
    The client to interact with making GOTO webinar API calls. This should
    live within a single request lifespan.
    """

    _access_token = None

    GOTO_BASE_URL = 'https://api.getgo.com/G2W/rest'

    ALL_WEBINARS = '/organizers/%s/webinars'
    WEBINAR_URL = '/organizers/%s/webinars/%s'
    UPCOMING_WEBINARS = '/organizers/%s/upcomingWebinars'

    WEBINAR_SESSIONS = '/organizers/%s/webinars/%s/sessions'
    WEBINAR_PROGRESS = '/organizers/%s/webinars/%s/attendees'
    SESSION_PROGRESS = '/organizers/%s/webinars/%s/sessions/%s/attendees'

    REGISTRANT = '/organizers/%s/webinars/%s/registrants/%s'
    REGISTRANTS = '/organizers/%s/webinars/%s/registrants'
    REGISTER_FIELDS = '/organizers/%s/webinars/%s/registrants/fields'

    def __init__(self, authorized_integration):
        self.authorized_integration = authorized_integration

    @Lazy
    def _access_token(self):
        return self.authorized_integration.access_token

    def _update_access_token(self):
        result = self.authorized_integration.update_tokens(self._access_token)
        self._access_token = result

    def _make_call(self, url, post_data=None, delete=False, acceptable_return_codes=None):
        if not acceptable_return_codes:
            acceptable_return_codes = (200,)
        url = '%s%s' % (self.GOTO_BASE_URL, url)

        def _do_make_call():
            access_header = 'Bearer %s' % self._access_token
            if post_data:
                return requests.post(url,
                                     json=post_data,
                                     headers={'Authorization': access_header,
                                              'Accept': 'application/json'})
            elif delete:
                return requests.delete(url,
                                       headers={'Authorization': access_header})
            else:
                return requests.get(url,
                                    headers={'Authorization': access_header})
        response = _do_make_call()
        if response.status_code in (401, 403):
            # Ok, expired token, refresh and try again.
            self._update_access_token()
            response = _do_make_call()

        if response.status_code not in acceptable_return_codes:
            logger.warn('Error while making webinar API call (%s) (%s) (%s)',
                        url,
                        response.status_code,
                        response.text)
            raise WebinarClientError(response.text)
        return response

    def get_all_webinars(self, raw=False):
        url = self.ALL_WEBINARS % self.authorized_integration.organizer_key
        result = self._make_call(url)
        if raw:
            return result.json()
        result = IWebinarCollection(result.json())
        return result.webinars

    def get_upcoming_webinars(self, raw=False):
        url = self.UPCOMING_WEBINARS % self.authorized_integration.organizer_key
        result = self._make_call(url)
        if raw:
            return result.json()
        result = IWebinarCollection(result.json())
        return result.webinars

    def get_webinar(self, webinar_key, raw=False):
        url = self.WEBINAR_URL % (self.authorized_integration.organizer_key, webinar_key)
        get_response = self._make_call(url, acceptable_return_codes=(200, 404))
        result = None
        if get_response.status_code != 404:
            if raw:
                result = get_response.json()
            else:
                result = IWebinar(get_response.json())
        return result

    def get_registration_fields(self, webinar_key):
        url = self.REGISTER_FIELDS % (self.authorized_integration.organizer_key, webinar_key)
        get_response = self._make_call(url, acceptable_return_codes=(200, 404))
        result = None
        if get_response.status_code != 404:
            result = IWebinarRegistrationFields(get_response.json())
        return result

    def register_user(self, user, webinar_key, registration_data):
        url = self.REGISTRANTS % (self.authorized_integration.organizer_key,
                                  webinar_key)
        # 409 if user is already registered
        response = self._make_call(url,
                                   post_data=registration_data,
                                   acceptable_return_codes=(201, 400, 409))
        if response.status_code == 400:
            raise WebinarRegistrationError(response.json())

        if response.status_code == 409:
            logger.info('User already registered for webinar')

        # We want to return a metadata object on 409 so we can store it if
        # we have not already.
        data = response.json()
        creator = user.username
        registrant_key = unicode(data.get('registrantKey'))
        data = {'join_url': data.get('joinUrl'),
                'registrant_key': registrant_key,
                'webinar_key': webinar_key,
                'organizer_key': self.authorized_integration.organizer_key,
                'creator': creator}
        return IWebinarRegistrationMetadata(data)

    def unregister_user(self, webinar_key, registrant_key):
        url = self.REGISTRANT % (self.authorized_integration.organizer_key,
                                 webinar_key,
                                 registrant_key)
        response = self._make_call(url, delete=True,
                                   acceptable_return_codes=(204, 404))
        result = response.status_code == 200
        return result

    def get_webinar_progress(self, webinar_key):
        url = self.WEBINAR_PROGRESS % (self.authorized_integration.organizer_key,
                                       webinar_key)
        get_response = self._make_call(url,
                                       acceptable_return_codes = (200, 404))
        result = None
        if get_response.status_code != 404:
            result = [IUserWebinarProgress(x) for x in get_response.json()]
        return result
