#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
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

from Testing.ZopeTestCase import user_name, folder_name
from Testing.ZopeTestCase import installProduct

from objectinteractiontestcase import ObjectInteractionInstaller, \
    setupPortal, ObjectInteractionTestCase

from CPSMailAccess.mailbox import manage_addMailBox
from CPSMailAccess.mailtool import manage_addMailTool
from CPSDefault.tests import CPSDefaultTestCase

installProduct('CPSMailAccess')

class ObjectInteractionTest(CPSDefaultTestCase.CPSDefaultTestCase):

    def afterSetUp(self):
        user = self.folder.acl_users.getUser(user_name)
        user.roles.append('Manager')

        # installing portal_webmail
        if not hasattr(self.portal, 'portal_webmail'):
            manage_addMailTool(self.portal)

    def test_getconnector(self):
        """ testing connector getter
        """
        container = self.portal
        manage_addMailBox(container, 'INBOX')

        mailbox = self.portal.INBOX

        mailbox['UID'] = 'tziade'
        mailbox['connection_type'] = 'IMAP'
        mailbox['password'] = 'secret'
        mailbox['HOST'] = 'localhost'

        connector = mailbox._getconnector()

        self.assertNotEquals(connector, None)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ObjectInteractionTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')



