#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from nti.app.products.acclaim import NT_EVIDENCE_NTIID_ID

from nti.app.products.acclaim.interfaces import IAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimIdEvidence
from nti.app.products.acclaim.interfaces import IAcclaimOrganization
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadge
from nti.app.products.acclaim.interfaces import IAcclaimBadgeCollection
from nti.app.products.acclaim.interfaces import IAcclaimOrganizationCollection
from nti.app.products.acclaim.interfaces import IAwardedAcclaimBadgeCollection

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.internalization import update_from_external_object

from nti.externalization.representation import WithRepr

from nti.ntiids.ntiids import is_valid_ntiid_string

from nti.ntiids.oids import to_external_ntiid_oid

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@component.adapter(dict)
@interface.implementer(IAcclaimIdEvidence)
def _acclaim_id_evidence_factory(ext):
    ext['ntiid'] = ext.get('id')
    obj = AcclaimIdEvidence()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IAcclaimOrganization)
def _acclaim_organization_factory(ext):
    if 'data' in ext:
        ext = ext['data']
    obj = AcclaimOrganization()
    ext['organization_id'] = ext['id']
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IAcclaimBadge)
def _acclaim_badge_factory(ext):
    if 'data' in ext:
        ext = ext['data']
    obj = AcclaimBadge()
    if 'owner' in ext:
        ext['organization_id'] = ext['owner'].get('id')
    ext['template_id'] = ext['id']
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IAwardedAcclaimBadge)
def _awarded_acclaim_badge_factory(ext):
    if 'data' in ext:
        ext = ext['data']
    ext['badge_template'] = IAcclaimBadge(ext['badge_template'])
    if 'evidence' in ext:
        # Only concerning ourselves with NT evidence
        evidence = ext['evidence'] or []
        new_evidence = []
        for evi in evidence:
            if      evi.get('name') == NT_EVIDENCE_NTIID_ID \
                and is_valid_ntiid_string(evi.get('id')):
                new_evidence.append(IAcclaimIdEvidence(evi))
        ext['evidence'] = new_evidence
    obj = AwardedAcclaimBadge()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IAcclaimBadgeCollection)
def _acclaim_badge_collection_factory(ext):
    obj = AcclaimBadgeCollection()
    metadata = ext['metadata']
    new_ext = dict()
    new_ext['badges'] = [IAcclaimBadge(x) for x in ext['data']]
    new_ext['badges_count'] = metadata.get('count')
    new_ext['total_badges_count'] = metadata.get('total_count')
    new_ext['current_page'] = metadata.get('current_page')
    new_ext['total_pages'] = metadata.get('total_pages')
    update_from_external_object(obj, new_ext)
    return obj


@component.adapter(dict)
@interface.implementer(IAwardedAcclaimBadgeCollection)
def _awarded_acclaim_badge_collection_factory(ext):
    obj = AwardedAcclaimBadgeCollection()
    metadata = ext['metadata']
    new_ext = dict()
    new_ext['badges'] = [IAwardedAcclaimBadge(x) for x in ext['data']]
    new_ext['badges_count'] = metadata.get('count')
    new_ext['total_badges_count'] = metadata.get('total_count')
    new_ext['current_page'] = metadata.get('current_page')
    new_ext['total_pages'] = metadata.get('total_pages')
    update_from_external_object(obj, new_ext)
    return obj


@component.adapter(dict)
@interface.implementer(IAcclaimOrganizationCollection)
def _acclaim_organization_collection_factory(ext):
    obj = AcclaimOrganizationCollection()
    new_ext = dict()
    new_ext['organizations'] = [IAcclaimOrganization(x) for x in ext['data']]
    update_from_external_object(obj, new_ext)
    return obj


@WithRepr
@interface.implementer(IAcclaimOrganization)
class AcclaimOrganization(PersistentCreatedAndModifiedTimeObject,
                          Contained,
                          SchemaConfigured):
    createDirectFieldProperties(IAcclaimOrganization)

    __parent__ = None
    __name__ = None

    mimeType = mime_type = "application/vnd.nextthought.acclaim.organization"


@WithRepr
@EqHash('template_id')
@interface.implementer(IAcclaimBadge, IAttributeAnnotatable)
class AcclaimBadge(PersistentCreatedAndModifiedTimeObject,
                   Contained,
                   SchemaConfigured):

    createDirectFieldProperties(IAcclaimBadge)

    mimeType = mime_type = "application/vnd.nextthought.acclaim.badge"

    __name__ = None
    __parent__ = None

    @property
    def ntiid(self):
        # Let's us be linkable
        return to_external_ntiid_oid(self)


@WithRepr
@interface.implementer(IAwardedAcclaimBadge)
class AwardedAcclaimBadge(SchemaConfigured):

    createDirectFieldProperties(IAwardedAcclaimBadge)

    mimeType = mime_type = "application/vnd.nextthought.acclaim.awardedbadge"


@interface.implementer(IAcclaimBadgeCollection)
class AcclaimBadgeCollection(SchemaConfigured):

    createDirectFieldProperties(IAcclaimBadgeCollection)

    mimeType = mime_type = "application/vnd.nextthought.acclaim.badgecollection"


@interface.implementer(IAwardedAcclaimBadgeCollection)
class AwardedAcclaimBadgeCollection(SchemaConfigured):

    createDirectFieldProperties(IAwardedAcclaimBadgeCollection)

    mimeType = mime_type = "application/vnd.nextthought.acclaim.awardedbadgecollection"


@interface.implementer(IAcclaimOrganizationCollection)
class AcclaimOrganizationCollection(SchemaConfigured):

    createDirectFieldProperties(IAcclaimOrganizationCollection)

    mimeType = mime_type = "application/vnd.nextthought.acclaim.organizationcollection"


@interface.implementer(IAcclaimIdEvidence)
class AcclaimIdEvidence(SchemaConfigured):

    createDirectFieldProperties(IAcclaimIdEvidence)

    mimeType = mime_type = "application/vnd.nextthought.acclaim.idevidence"

    id = alias('ntiid')

    type = u'IdEvidence'
