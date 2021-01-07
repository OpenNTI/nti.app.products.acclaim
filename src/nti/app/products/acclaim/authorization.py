#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.security.permission import Permission

logger = __import__('logging').getLogger(__name__)


ACT_ACCLAIM = Permission('nti.actions.acclaim')
