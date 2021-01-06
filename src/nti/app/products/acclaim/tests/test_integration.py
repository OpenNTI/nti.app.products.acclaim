#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import contains_inanyorder

from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from nti.app.testing.webtest import TestApp

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
    def test_integration(self):
        """
        Test enabling acclaim integration and editing.
        """
        admin_username = 'acclaim_int@nextthought.com'
        site_admin_username = 'acclaim_site_admin'
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(admin_username)
            self._assign_role_for_site(ROLE_ADMIN, admin_username)
            self._create_user(site_admin_username)
        with mock_dataserver.mock_db_trans(self.ds, site_name="mathcounts.nextthought.com"):
            self._assign_role_for_site(ROLE_SITE_ADMIN, site_admin_username)

        admin_env = self._make_extra_environ(admin_username)
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
        res = self.testapp.post(enable_href,
                                {'authorization_token', 'acclaim_authorization_token'},
                                extra_environ=site_admin_env)
        from IPython.terminal.debugger import set_trace;set_trace()

        self.testapp.post(enable_href,
                          {'authorization_token', 'acclaim_authorization_token'},
                          extra_environ=site_admin_env,
                          status=422)
