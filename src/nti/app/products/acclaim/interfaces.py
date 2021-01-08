#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from nti.app.products.integration.interfaces import IIntegration

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.coremetadata.interfaces import IShouldHaveTraversablePath

from nti.schema.field import Int
from nti.schema.field import Bool
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import HTTPURL
from nti.schema.field import ValidText
from nti.schema.field import ListOrTuple
from nti.schema.field import ValidDatetime
from nti.schema.field import DecodingValidTextLine as ValidTextLine


class IAcclaimIntegration(IIntegration, ICreated, ILastModified, IShouldHaveTraversablePath):
    """
    Acclaim integration
    """

    authorization_token = ValidTextLine(title=u'authorization token',
                                        description=u"Acclaim integration authorization token",
                                        min_length=1)


class IAcclaimClient(interface.Interface):
    """
    A webinar client to fetch webinar information.
    """

    def get_badge(badge_template_id):
        """
        Get the :class:`IAcclaimBadge` associated with the template id.
        """

    def get_badges(sort=None, filters=None, page=None):
        """
        Return an :class:`IAcclaimBadgeCollection`.

        https://www.youracclaim.com/docs/badge_templates
        """

    def get_awarded_badges(user, sort=None, filters=None, page=None):
        """
        Return an :class:`IAwardedAcclaimBadgeCollection`.

        https://www.youracclaim.com/docs/issued_badges filtered by user email.
        """

    def award_badge(user, badge_template_id, suppress_badge_notification_email, locale):
        """
        Award a badge to a user.

        https://www.youracclaim.com/docs/issued_badges
        """

    def revoke_badge(user, badge_id, reason):
        """
        Revoke a badge awarded to a user.

        https://www.youracclaim.com/docs/issued_badges#revoke-a-badge
        """


class IAcclaimBadge(IShouldHaveTraversablePath, IAttributeAnnotatable):
    """
    An Acclaim badge template.
    """

    template_id = ValidText(title=u"Template id",
                            required=True)

    allow_duplicate_badges = Bool(title=u"Allow duplicate badges",
                                  description=u'Badge can be awarded to a user multiple times',
                                  required=True)

    description = ValidTextLine(title=u"Description",
                                required=False)

    name = ValidTextLine(title=u"Badge name",
                         required=True)

    state = ValidTextLine(title=u"Badge state",
                          description=u"State - active, archived, draft",
                          required=False)

    badges_count = Int(title=u"Awarded badges count",
                       required=False)

    public = Bool(title=u"Badge is public",
                  required=True)

    visibility = ValidTextLine(title=u"Badge visibility",
                               required=True)

    image_url = HTTPURL(title=u"Badge image url",
                        required=False)

    created_at = ValidDatetime(title=u"Badge created date",
                               required=True)

    updated_at = ValidDatetime(title=u"Badge last modified",
                               required=True)


class IAwardedAcclaimBadge(IShouldHaveTraversablePath, IAttributeAnnotatable):

    badge_template = Object(IAcclaimBadge,
                            title=u'The Acclaim badge template.',
                            required=True)

    image_url = HTTPURL(title=u"Badge image url",
                        required=False)

    created_at = ValidDatetime(title=u"Badge created date",
                               required=True)

    updated_at = ValidDatetime(title=u"Badge last modified",
                               required=True)

    public = Bool(title=u"Badge is public",
                  required=True)

    locale = ValidTextLine(title=u"Badge user locale",
                           required=True)

    recipient_email = ValidTextLine(title=u"Badge user email",
                                    required=True)


class IAcclaimBadgeCollection(interface.Interface):

    badges = ListOrTuple(Object(IAcclaimBadge),
                         title=u"Acclaim badges",
                         required=True,
                         min_length=0)

    badges_count = Int(title=u"Badge count",
                       required=True)

    total_badges_count = Int(title=u"Total badges count",
                             required=False)

    current_page = Int(title=u"Current page",
                       required=True)

    total_pages = Int(title=u"Total page count",
                      required=True)

    accept_badge_url = HTTPURL(title=u"Accept badge URL",
                               required=False)


class IAwardedAcclaimCollection(interface.Interface):

    badges = ListOrTuple(Object(IAwardedAcclaimBadge),
                         title=u"Awarded Acclaim badges",
                         required=True,
                         min_length=0)


class AcclaimClientError(Exception):

    def __init__(self, msg, json=None):
        Exception.__init__(self, msg)
        self.json = json
