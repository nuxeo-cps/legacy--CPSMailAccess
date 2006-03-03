# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2006 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
import unittest
import os

from zope.interface import implements
from zope.app import zapi

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.Five import zcml

import Products
from Products.CPSMailAccess.exportimport import CPSMailAccessXMLAdapter
from Products.CPSMailAccess.mailtool import MailTool

current_dir = os.path.dirname(__file__)
wanted_xml = os.path.join(current_dir, 'wanted.xml')

_MAILACCESS_BODY = unicode(open(wanted_xml).read())

class DummyLogger:

    def __init__(self, id, messages):
        self._id = id
        self._messages = messages

    def info(self, msg, *args, **kwargs):
        self._messages.append((20, self._id, msg))

    def warning(self, msg, *args, **kwargs):
        self._messages.append((30, self._id, msg))

class DummySetupEnviron(object):
    """Context for body im- and exporter.
    """
    implements(ISetupEnviron)

    def __init__(self):
        self._notes = []
        self._should_purge = True

    def getLogger(self, name):
        return DummyLogger(name, self._notes)

    def shouldPurge(self):
        return self._should_purge

class ExportImportTestCase(BodyAdapterTestCase):

    def assertXMLEqual(self, xml1, xml2):
        def _clean(xml):
            xml = xml.replace('\n', '')
            xml = xml.replace('\t', '')
            xml = xml.replace('  ', '')

        self.assertEqual(_clean(xml1), _clean(xml2))

    def test_body_set(self):
        context = DummySetupEnviron()
        adapted = zapi.getMultiAdapter((self._obj, context), IBody)
        adapted.body = self._BODY
        self._verifyImport(self._obj)
        self.assertXMLEqual(adapted.body, self._BODY)

        # now in update mode
        context._should_purge = False
        adapted = zapi.getMultiAdapter((self._obj, context), IBody)
        adapted.body = self._BODY
        self._verifyImport(self._obj)
        self.assertXMLEqual(adapted.body, self._BODY)

        # and again in update mode
        adapted = zapi.getMultiAdapter((self._obj, context), IBody)
        adapted.body = self._BODY
        self._verifyImport(self._obj)
        self.assertXMLEqual(adapted.body, self._BODY)

    def test_body_get(self):
        self._populate(self._obj)
        context = DummySetupEnviron()
        adapted = zapi.getMultiAdapter((self._obj, context), IBody)
        self.assertXMLEqual(adapted.body, self._BODY)

    def _getTargetClass(self):
        return CPSMailAccessXMLAdapter

    def _verifyImport(self, obj):
        pass

    def setUp(self):
        BodyAdapterTestCase.setUp(self)
        zcml.load_config('exportimport.zcml', Products.CPSMailAccess)

        self._obj = MailTool()
        self._BODY = _MAILACCESS_BODY

    def test_serialization(self):
        adapter = CPSMailAccessXMLAdapter(MailTool(), DummySetupEnviron())
        fragment = adapter._doc.createDocumentFragment()
        sequence = (1, 'ok', 12, .5)
        adapter._sequenceToXML(fragment, sequence)
        result = adapter._XMLToSequence(fragment.childNodes[0])
        self.assertEquals(tuple(result), sequence)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ExportImportTestCase)
        ))
