#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
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
import unittest
from zope.testing import doctest
from basetestcase import MailTestCase
from Products.CPSMailAccess.adressbook import AddressBookViewer
from OFS.Folder import Folder

class FakeDirectory(Folder):
    pass

class FakeDirectoryTool(Folder):

    members = FakeDirectory()
    addressbook = FakeDirectory()

    def listVisibleDirectories(self):
        return ['members', 'roles', 'groups', 'addressbook']

    def searchEntries(self, dir_, return_fields=None, **kw):

        return [{'id': 'tarek', 'fullname' : 'Tarek Ziadé'}]

class AddressBookTestCase(MailTestCase):

    def __init__(self, methodName='runTest'):
        MailTestCase.__init__(self, methodName)
        self.portal.portal_directory = FakeDirectoryTool()

    def test_instanciate(self):
        ob = AddressBookViewer(None, None)
        self.assertNotEquals(ob, None)

    def oldtest_gettingentries(self):
        mailbox = self._getMailBox()

        # patching
        mailbox._searchEntries = self.portal.portal_directory.searchEntries

        ob = AddressBookViewer(mailbox, self.request)
        self.assertNotEquals(ob, None)

        self.assertEquals(ob.getEntries(), [[{'fullname': 'Tarek Ziad\xe9',
                                              'id': 'tarek'}],
                                            [{'fullname': 'Tarek Ziad\xe9',
                                              'id': 'tarek'}]])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(AddressBookTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.adressbook'),
        ))
