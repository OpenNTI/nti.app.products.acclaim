#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_entries

import fudge

from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from nti.app.products.acclaim.client_models import AcclaimOrganization
from nti.app.products.acclaim.client_models import AcclaimOrganizationCollection

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.authorization import ROLE_ADMIN
from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.tests import mock_dataserver


class TestIntegration(ApplicationLayerTest):

    default_origin = 'http://mathcounts.nextthought.com'

    def _assign_role_for_site(self, role, username, site=None):
        role_manager = IPrincipalRoleManager(site or getSite())
        role_name = getattr(role, "id", role)
        role_manager.assignRoleToPrincipal(role_name, username)

    @WithSharedApplicationMockDS(users=True, testapp=True)
    @fudge.patch('nti.app.products.acclaim.views.AcclaimIntegrationUpdateMixin._get_organizations')
    def test_integration(self, mock_get_orgs):
        """
        Test enabling acclaim integration and editing.
        """
        org_collection = AcclaimOrganizationCollection()
        org = AcclaimOrganization(organization_id='test_org_id')
        org_collection.organizations = [org]

        mock_get_orgs.is_callable().returns(org_collection)
        admin_username = 'acclaim_int@nextthought.com'
        site_admin_username = 'acclaim_site_admin'
        other_username = 'acclaim_int_other'
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(other_username)
            self._create_user(admin_username)
            self._assign_role_for_site(ROLE_ADMIN, admin_username)
            self._create_user(site_admin_username)
        with mock_dataserver.mock_db_trans(self.ds, site_name="mathcounts.nextthought.com"):
            self._assign_role_for_site(ROLE_SITE_ADMIN, site_admin_username)

        admin_env = self._make_extra_environ(admin_username)
        other_env = self._make_extra_environ(other_username)
        site_admin_env = self._make_extra_environ(site_admin_username)

        def _get_acclaim_int(username, env):
            url = "/dataserver2/users/%s/Integration/Integrations" % username
            res = self.testapp.get(url, extra_environ=env)
            res = res.json_body
            acclaim_int = next((x for x in res['Items'] if x.get('Class') == 'AcclaimIntegration'), None)
            return acclaim_int

        acclaim_int = _get_acclaim_int(site_admin_username, site_admin_env)
        assert_that(acclaim_int, not_none())
        enable_href = self.require_link_href_with_rel(acclaim_int, 'enable')

        acclaim_int = _get_acclaim_int(admin_username, admin_env)
        assert_that(acclaim_int, not_none())
        self.require_link_href_with_rel(acclaim_int, 'enable')

        # Enable integration
        self.testapp.post_json(enable_href,
                               {'authorization_token': 'acclaim_authorization_token'},
                               extra_environ=other_env,
                               status=403)

        res = self.testapp.post_json(enable_href,
                                     {'authorization_token': 'acclaim_authorization_token'},
                                     extra_environ=site_admin_env)
        res = res.json_body
        acclaim_href = res.get('href')
        assert_that(acclaim_href, not_none())
        assert_that(res, has_entries('CreatedTime', not_none(),
                                     'NTIID', not_none(),
                                     'authorization_token', '******************ion_token',
                                     'Creator', 'acclaim_site_admin',
                                     'Last Modified', not_none(),
                                     'organization', has_entry('organization_id', 'test_org_id')))

        disconnect_href = self.require_link_href_with_rel(res, 'disconnect')

        # Can not re-enable
        self.testapp.post_json(enable_href,
                               {'authorization_token': 'acclaim_authorization_token'},
                               extra_environ=site_admin_env,
                               status=422)

        self.testapp.put_json(acclaim_href,
                              {'authorization_token': 'new_token'},
                              extra_environ=other_env,
                              status=403)

        # Change orgs
        org = AcclaimOrganization(organization_id='test_org_id2')
        org_collection.organizations = [org]
        # Edit and update toke also fetches new orgs
        res = self.testapp.put_json(acclaim_href,
                                    {'authorization_token': 'new_token'},
                                    extra_environ=site_admin_env)
        res = res.json_body
        assert_that(res, has_entries('authorization_token', '******ken',
                                     'organization', has_entry('organization_id', 'test_org_id2')))

        self.testapp.get(acclaim_href, extra_environ=other_env, status=403)
        self.testapp.get(acclaim_href, extra_environ=admin_env)
        self.testapp.get(acclaim_href, extra_environ=site_admin_env)

        self.testapp.delete(disconnect_href, extra_environ=other_env, status=403)
        self.testapp.delete(disconnect_href, extra_environ=admin_env)
        self.testapp.delete(disconnect_href, extra_environ=site_admin_env, status=404)
