#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_properties

import os
import unittest
import simplejson

from nti.testing.matchers import verifiably_provides

from nti.externalization.externalization import to_external_object

from nti.app.products.acclaim import NT_EVIDENCE_NTIID_ID

from nti.app.products.acclaim.tests import SharedConfiguringTestLayer

from nti.app.products.acclaim.interfaces import IAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimOrganization
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimBadgeCollection
from nti.app.products.acclaim.interfaces import IAcclaimOrganizationCollection
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadgeCollection


class TestAcclaimClientInternalization(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _load_resource(self, name):
        path = os.path.join(os.path.dirname(__file__), 'data', name)
        with open(path, "r") as fp:
            data = unicode(fp.read())
            source = simplejson.loads(data)
        return source

    def test_badge(self):
        template_json = self._load_resource('template.json')
        badge = IAcclaimBadge(template_json)
        assert_that(badge, verifiably_provides(IAcclaimBadge))

        assert_that(badge.organization_id, is_(u'b4deef45-9e00-4809-be6b-a6835a8f350e'))
        assert_that(badge.template_id, is_(u"823a5e0c-1d8d-4801-a5c8-bd4e3a776a4c"))
        assert_that(badge.allow_duplicate_badges, is_(True))
        assert_that(badge.description, is_(u"Dynamically deliver go forward e-tailers"))
        assert_that(badge.name, is_(u"Badge Template 7"))
        assert_that(badge.state, is_(u'active'))
        assert_that(badge.badges_count, is_(0))
        assert_that(badge.public, is_(True))
        assert_that(badge.visibility, is_('public'))
        assert_that(badge.image_url, is_(u"https://cdn.example.com/path/to/image.png"))
        assert_that(badge.created_at, not_none())
        assert_that(badge.updated_at, not_none())
        assert_that(badge.badge_url, is_(u"https://www.youracclaim.com/org/organization-5/badge/badge-template-7"))

        badge_ext = to_external_object(badge)
        assert_that(badge_ext, has_entries('organization_id', u'b4deef45-9e00-4809-be6b-a6835a8f350e',
                                           'template_id', u"823a5e0c-1d8d-4801-a5c8-bd4e3a776a4c",
                                           'allow_duplicate_badges', True,
                                           'description', u"Dynamically deliver go forward e-tailers",
                                           'name', u"Badge Template 7",
                                           'badges_count', 0,
                                           'public', True,
                                           'visibility', 'public',
                                           'image_url', u"https://cdn.example.com/path/to/image.png",
                                           'created_at', not_none(),
                                           'updated_at', not_none()))

    def test_badge_collection(self):
        template_json = self._load_resource('template_collection.json')
        collection = IAcclaimBadgeCollection(template_json)
        assert_that(collection, verifiably_provides(IAcclaimBadgeCollection))
        assert_that(collection.badges, has_length(2))
        assert_that(collection.badges_count, is_(2))
        assert_that(collection.total_badges_count, is_(2))
        assert_that(collection.current_page, is_(1))
        assert_that(collection.total_pages, is_(1))

        collection_ext = to_external_object(collection)
        assert_that(collection_ext, has_entries('Items', has_length(2),
                                                'badges_count', 2,
                                                'total_badges_count', 2,
                                                'current_page', 1,
                                                'total_pages', 1))

    def test_awarded_badge(self):
        template_json = self._load_resource('issued_badges.json')
        collection = IAwardedAcclaimBadgeCollection(template_json)
        assert_that(collection, verifiably_provides(IAwardedAcclaimBadgeCollection))
        assert_that(collection.badges, has_length(1))
        assert_that(collection.badges_count, is_(1))
        assert_that(collection.total_badges_count, is_(1))
        assert_that(collection.current_page, is_(1))
        assert_that(collection.total_pages, is_(1))

        awarded_badge = collection.badges[0]
        assert_that(awarded_badge, verifiably_provides(IAwardedAcclaimBadge))
        assert_that(awarded_badge.badge_template.organization_id, is_(u'20be75f6-4b33-4609-a1dd-9c340afa1a8f'))
        assert_that(awarded_badge.badge_template.template_id, is_(u"09d1ac8b-d097-4ae4-844a-a2ae01d1bdbe"))
        assert_that(awarded_badge.badge_template.description, is_(u"Dynamically deliver go forward e-tailers"))
        assert_that(awarded_badge.accept_badge_url, none())
        assert_that(awarded_badge.recipient_email, is_(u"user10001@example.com"))
        assert_that(awarded_badge.locale, is_('en'))
        assert_that(awarded_badge.public, is_(True))
        assert_that(awarded_badge.state, is_('accepted'))
        assert_that(awarded_badge.image_url, is_(u"https://cdn.example.com/path/to/image.png"))
        assert_that(awarded_badge.badge_url, is_(u"https://localhost/badges/749daf6e-4dbc-4b47-b401-b7e0477e0284"))
        assert_that(awarded_badge.created_at, not_none())
        assert_that(awarded_badge.updated_at, not_none())
        assert_that(awarded_badge.evidence, has_length(1))
        assert_that(awarded_badge.evidence[0], has_properties('ntiid', 'tag:nextthought.com,2011-10:aaron.eskam@nextthought.com-OID-0x0c3a2781:5573657273:ScMA6PZxJDH',
                                                              'name', NT_EVIDENCE_NTIID_ID,
                                                              'type', 'IdEvidence'))

        collection_ext = to_external_object(collection)
        assert_that(collection_ext, has_entries('Items', has_length(1),
                                                'badges_count', 1,
                                                'total_badges_count', 1,
                                                'current_page', 1,
                                                'total_pages', 1))
        badge_ext = collection_ext['Items'][0]
        assert_that(badge_ext, has_entries('recipient_email', u"user10001@example.com",
                                           'locale', u"en",
                                           'public', True,
                                           'state', 'accepted',
                                           'badge_url', u"https://localhost/badges/749daf6e-4dbc-4b47-b401-b7e0477e0284",
                                           'image_url', u"https://cdn.example.com/path/to/image.png",
                                           'created_at', not_none(),
                                           'updated_at', not_none()))
        evidence = badge_ext.get('evidence')
        assert_that(evidence, has_length(1))
        evidence = evidence[0]
        assert_that(evidence, has_entries('ntiid', "tag:nextthought.com,2011-10:aaron.eskam@nextthought.com-OID-0x0c3a2781:5573657273:ScMA6PZxJDH",
                                          'Class', u"AcclaimIdEvidence",
                                          'name', NT_EVIDENCE_NTIID_ID))
        badge_ext = badge_ext.get('badge_template')
        assert_that(badge_ext, not_none())
        assert_that(badge_ext, has_entries('organization_id', u'20be75f6-4b33-4609-a1dd-9c340afa1a8f',
                                           'template_id', u"09d1ac8b-d097-4ae4-844a-a2ae01d1bdbe",
                                           'description', u"Dynamically deliver go forward e-tailers"))

    def test_organization(self):
        template_json = self._load_resource('organization_collection.json')
        collection = IAcclaimOrganizationCollection(template_json)
        assert_that(collection, verifiably_provides(IAcclaimOrganizationCollection))
        assert_that(collection.organizations, has_length(1))

        org = collection.organizations[0]
        assert_that(org, verifiably_provides(IAcclaimOrganization))
        assert_that(org.organization_id, is_(u"ba92621f-f22c-41e5-9157-c2dc274e3cf0"))
        assert_that(org.name, is_(u'Organization 8'))
        assert_that(org.photo_url, is_(u"https://cdn.example.com/path/to/image.png"))
        assert_that(org.website_url, is_(u"http://www.example.com/"))
        assert_that(org.contact_email, is_(u"hello8@example.com"))

        collection_ext = to_external_object(collection)
        assert_that(collection_ext, has_entries('organizations', has_length(1)))
        org_ext = collection_ext['organizations'][0]
        assert_that(org_ext, has_entries('organization_id', u"ba92621f-f22c-41e5-9157-c2dc274e3cf0",
                                         'name', u'Organization 8',
                                         'photo_url', u"https://cdn.example.com/path/to/image.png",
                                         'website_url', u"http://www.example.com/",
                                         'contact_email', u"hello8@example.com"))
