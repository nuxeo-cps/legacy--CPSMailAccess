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
from CPSMailAccess.mailbox import manage_addMailBox
from CPSMailAccess.mailtool import manage_addMailTool, MailTool
from CPSMailAccess.mailfolder import MailFolder
from Products.CPSMailAccess.mailexceptions import MailContainerError
from CPSMailAccess.utils import uniqueId
from CPSMailAccess.mailbox import MailBox, MailBoxParametersView
from Acquisition import Implicit
from Testing.ZopeTestCase import ZopeTestCase

class FakePortal(Implicit):
    def this(self):
        return self

    def _setObject(self, id, ob):
        setattr(self, id, ob)

fakePortal = FakePortal()
portal_webmail = MailTool()
fakePortal.portal_webmail = portal_webmail

class ObjectInteractionTest(ZopeTestCase):
    msg_key = 0

    def __init__(self, methodName='runTest'):
        ZopeTestCase.__init__(self, methodName)
        self.portal = fakePortal

    def msgKeyGen(self):
        result = 'msg_' + str(self.msg_key)
        self.msg_key += 1
        return result

    def afterSetUp(self):
        user = self.folder.acl_users.getUser(user_name)
        user.roles.append('Manager')

        # installing portal_webmail
        if not hasattr(self.portal, 'portal_webmail'):
            manage_addMailTool(self.portal)

    def _getMailBox(self):
        """ testing connector getter
        """
        container = fakePortal
        manage_addMailBox(container, 'INBOX')
        mailbox = self.portal.INBOX
        mailbox.connection_params['uid'] = 'tziade'
        mailbox.connection_params['connection_type'] = 'IMAP'
        mailbox.connection_params['password'] = 'secret'
        mailbox.connection_params['HOST'] = 'localhost'
        return mailbox


    def test_getconnectors(self):
        # testing connector getter thru portal_webmail
        wm = self.portal.portal_webmail
        ct = wm.listConnectionTypes()
        self.assertNotEqual(ct, [])


    def test_getconnector(self):
        # testing connector getter thru local mailbox
        mailbox = self._getMailBox()
        connector = mailbox._getconnector()
        self.assertNotEquals(connector, None)

    def test_synchro(self):
        # testing synchro
        mailbox = self._getMailBox()
        mailbox.synchronize()

    def test_containtment(self):
        # testing containtment
        mailbox = self._getMailBox()

        folder = mailbox._addFolder()
        self.assertNotEquals(folder._getconnector(), None)

        folder = MailFolder()
        self.failUnlessRaises(MailContainerError, folder._getconnector)

    def test_synchronize(self):
        # testing synchronize calls
        mailbox = self._getMailBox()

        for i in range(10):
            ob = mailbox._addFolder()

            for i in range(10):
                ob._addFolder()

            for i in range(123):
                key = self.msgKeyGen()
                ob._addMessage(key, key)

        mailbox.synchronize()

    def test_uniqueId(self):
        # testing unique ID
        mailbox = self._getMailBox()
        id = uniqueId(mailbox, 'folder_', use_primary=False)
        self.assertEquals(hasattr(mailbox, id), False)

        mailbox._addFolder(id, id)

        id = uniqueId(mailbox, 'folder_', use_primary=False)
        self.assertEquals(hasattr(mailbox, id), False)

    def test_syncdirs(self):
        # testing folder synchro
        mailbox = self._getMailBox()

        # first synchronize to create structure
        mailbox._syncdirs([{'Name' : 'INBOX.Lop', 'Attributes' : ''},
                           {'Name' : 'INBOX.One', 'Attributes' : ''},
                           {'Name' : 'INBOX.[BCEAO]', 'Attributes' : ''},
                           {'Name' : 'Trash', 'Attributes' : ''}])

        self.assertEquals(hasattr(mailbox, 'INBOX'), True)

        inbox = mailbox.INBOX

        self.assertEquals(hasattr(inbox, 'Lop'), True)
        self.assertEquals(hasattr(inbox, 'One'), True)
        self.assertEquals(hasattr(inbox, 'BCEAO'), True) # we are looking to ids not titles
        self.assertEquals(hasattr(inbox, 'Trash'), True)

        folders = mailbox.getMailMessages(True, False, True)

        self.assertEquals(len(folders), 5)

        # now removes Trash
        mailbox._syncdirs([{'Name' : 'INBOX', 'Attributes' : ''},
                           {'Name' : 'INBOX.One', 'Attributes' : ''},
                           {'Name' : 'INBOX.[BCEAO]', 'Attributes' : ''}])

        folders = mailbox.getMailMessages(True, False, True)

        self.assertEquals(len(folders), 3)
        self.assertEquals(hasattr(folders, 'Trash'), False)

    def test_MailBoxParametersInterface(self):
        # testing MailBoxParametersView parameters interface
        mailbox = self._getMailBox()
        view = MailBoxParametersView(mailbox, None)
        params = {'connection_type' : 'DUMMY',
            'uid' : 'tarek', 'ok': '12', 'submit' : 'ok'}
        view.setParameters(params)
        self.assertEquals(mailbox.connection_params['ok'], '12')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ObjectInteractionTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')



