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
from Products.CPSMailAccess.directorypicker import DirectoryPicker
from OFS.Folder import Folder

class FakeDirectory(Folder):
    pass

class FakeDirectoryTool(Folder):

    members = FakeDirectory()

    def listVisibleDirectories(self):
        return ['members', 'roles', 'groups']

    def searchEntries(self, directory_name, return_fields, **kw):

        return [{'id': 'tarek', 'fullname' : 'Tarek Ziadé'}]

class DirectoryPickerTestCase(MailTestCase):

    def __init__(self, methodName='runTest'):
        MailTestCase.__init__(self, methodName)
        self.portal.portal_directory = FakeDirectoryTool()

    def test_instanciate(self):
        ob = DirectoryPicker(None)
        self.assertNotEquals(ob, None)

    def test_getDirectoryInfos(self):
        # use story
        # cps provide me a portal_directory
        portal_dir = self.portal.portal_directory

        # lets' adapt it
        ob = DirectoryPicker(portal_dir)

        # i need to get a member's entry
        # let's see if it's listed
        list_ = ob.getDirectoryList()
        self.assert_(list_.index('members') != -1)

        # ok now let's get all members entry
        entries = ob.searchEntries('members')
        self.assertNotEquals(entries, None)





def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DirectoryPickerTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.directorypicker'),
        ))
