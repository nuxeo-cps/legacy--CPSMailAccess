#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
#         Tarek Ziadé <tz@nuxeo.com>
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
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
from Products.CPSMailAccess.mailfolder import MailFolder
from Products.CPSMailAccess.mailexceptions import MailContainerError
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailbox import MailBox
from Products.CPSMailAccess.interfaces import IMailFolder, IMailMessage
from basetestcase import MailTestCase

class MailFolderTestCase(MailTestCase):

    def test_getMailBox(self):
        mailbox = self._getMailBox()
        mailbox._addFolder('folder')
        folder = mailbox.folder
        self.assertEquals(folder.getMailBox(), mailbox)

    def test_getServerName(self):
        # testing getServerName and setServerName
        # this is trivial but will be very useful
        # when setServerName will call for content resync
        # for non-regression
        ob = MailFolder()
        ob.setServerName('INBOX')
        self.assertEquals(ob.getServerName(), 'INBOX')
        ob.setServerName('INBOX.Sent')
        self.assertEquals(ob.getServerName(), 'INBOX.Sent')


    def test_getMailMessages(self):
        # testing getMailMessages with all combos
        ob = self.test_getMailMessagesCount()

        all_types = ob.getMailMessages()
        self.assertEquals(len(all_types), 133)

        messages_types = ob.getMailMessages(False, True)

        # see if transtyping is ok
        for element in messages_types:
            self.assertEquals(IMailMessage.providedBy(element), True)

        folder_types = ob.getMailMessages(True, False)

        # see if transtyping is ok
        for element in folder_types:
            self.assertEquals(IMailFolder.providedBy(element), True)

        no_type = ob.getMailMessages(False, False)

        self.assertEquals(len(no_type), 0)

    def test_getMailMessagesCount(self):
        # testing getMailMessagesCount with all combos
        ob = MailFolder()

        for i in range(10):
            ob._addFolder()

        for i in range(123):
            key = self.msgKeyGen()
            ob._addMessage(key, key)

        count = ob.getMailMessagesCount(True, True)
        self.assertEquals(count, 133)

        count = ob.getMailMessagesCount(False, True)
        self.assertEquals(count, 123)

        count = ob.getMailMessagesCount(True, False)
        self.assertEquals(count, 10)

        count = ob.getMailMessagesCount(False, False)
        self.assertEquals(count, 0)

        # for reuse
        return ob


    def test_getMailMessagesRecursive(self):
        # testing getMailMessages with all combos recursively
        ob = self.test_getMailMessagesCountRecursive()
        all_types = ob.getMailMessages(True, True, True)
        self.assertEquals(len(all_types), 263)
        messages_types = ob.getMailMessages(False, True, True)

        # see if transtyping is ok
        for element in messages_types:
            self.assertEquals(IMailMessage.providedBy(element), True)

        folder_types = ob.getMailMessages(True, False,True)
        # see if transtyping is ok
        for element in folder_types:
            self.assertEquals(IMailFolder.providedBy(element), True)

        no_type = ob.getMailMessages(False, False, True)
        self.assertEquals(len(no_type), 0)


    def test_getMailMessagesCountRecursive(self):
        # testing getMailMessagesCount with all combos recursively
        ob = MailFolder()

        for i in range(10):
            folder = ob._addFolder('folder_'+str(i), 'folder_'+str(i))
            key = self.msgKeyGen()
            folder._addMessage(key,key)
            for y in range(2):
                subfolder = folder._addFolder()
                for y in range(5):
                    key = self.msgKeyGen()
                    subfolder._addMessage(key, key)

        for i in range(123):
            key = self.msgKeyGen()
            ob._addMessage(key, key)

        count = ob.getMailMessagesCount(True, True, True)
        self.assertEquals(count, 263)

        count = ob.getMailMessagesCount(False, True, True)
        self.assertEquals(count, 233)

        count = ob.getMailMessagesCount(True, False, True)
        self.assertEquals(count, 30)

        count = ob.getMailMessagesCount(False, False, True)
        self.assertEquals(count, 0)

        # for reuse
        return ob

    def test_childFoldersCount(self):
        # testing child folder count
        ob = self.test_getMailMessagesCountRecursive()
        count = ob.childFoldersCount()
        self.assertEquals(count, 10)

    def test_childFoldersCount(self):
        # testing child folder count
        ob = self.test_getMailMessagesCountRecursive()
        childs = ob.getchildFolders()
        self.assertEquals(len(childs), 10)

    def test_setSyncState(self):
        # testing setSyncState
        ob = MailFolder()
        for i in range(5):
            sub_folder = ob._addFolder()
            for y in range(4):
                sub_sub_folder = sub_folder._addFolder()
        ob.setSyncState(state=False, recursive=True)
        folders = ob.getMailMessages(True, False, True)
        self.assertEquals(len(folders), 25)
        for folder in folders:
            self.assertEquals(folder.sync_state, False)
        ob.setSyncState(state=True, recursive=True)
        folders = ob.getMailMessages(True, False, True)
        for folder in folders:
            self.assertEquals(folder.sync_state, True)

    def test_isEmpty(self):
        ob = MailFolder()
        self.assert_(ob.isEmpty())
        for i in range(10):
            ob._addFolder()
        self.assert_(not ob.isEmpty())

    def test_childFoldersCount(self):
        ob = MailFolder()
        self.assertEquals(ob.childFoldersCount(), 0)
        for i in range(10):
            ob._addFolder()
        for i in range(10):
            ob._addMessage('ok'+str(i), 'ok'+str(i))
        self.assertEquals(ob.childFoldersCount(), 10)

    def oldtest_renaming(self):
        mailbox = self._getMailBox()
        Todos = mailbox._addFolder('Todos', 'Todos')
        res = Todos.rename('Done')
        self.assertEquals(Todos.server_name, 'Done')
        self.assert_(hasattr(mailbox, 'Done'))
        self.assert_(not hasattr(mailbox, 'Todos'))

    def test_simpleFolderName(self):
        mailbox = self._getMailBox()
        ob = MailFolder('Todos')
        mailbox._setObject('Todos', ob)
        ob = mailbox.Todos
        ob.server_name = 'INBOX.Todos'
        self.assertEquals(ob.simpleFolderName(), 'Todos')

    def oldtest_folder_deleting(self):
        mailbox = self._getMailBox()
        Trash = mailbox._addFolder('Trash')

        mailbox.emptyTrash()

        Todos = mailbox._addFolder('Todosez', 'Todosez')
        # setting up the trash

        res = Todos.delete()
        self.assertEquals(Todos.server_name, 'INBOX.Trash.Todosez')
        self.assert_(hasattr(mailbox.Trash, 'Todosez'))
        self.assertEquals(mailbox.Trash.Todos.getMailFolder().id, 'Trash')

    def test_message_moving(self):
        mailbox = self._getMailBox()
        msg1 = mailbox._addMessage('1', '1234567TCFGVYBH')
        self.assertEquals(msg1.getMailFolder(), mailbox)
        # setting up the trash
        Trash = mailbox._addFolder('Trash')
        msg1 = mailbox._moveMessage(msg1.uid, Trash)
        self.assertNotEquals(getattr(Trash, '.1', None), None)
        self.assertEquals(getattr(mailbox, '.1', None), None)

        self.assertEquals(msg1.getMailFolder(), Trash)

    def test_message_moving_with_IMAP(self):
        mailbox = self._getMailBox()
        msg1 = mailbox._addMessage('1', '1234567TCFGVYBH')
        self.assertEquals(msg1.getMailFolder(), mailbox)
        # setting up the trash
        Trash = mailbox._addFolder('Trash')
        mailbox.moveMessage(msg1.uid, Trash)
        self.assertNotEquals(getattr(Trash, '.1', None), None)
        self.assertEquals(getattr(mailbox, '.1', None), None)

    def test_id_generator(self):
        mailbox = self._getMailBox()
        msg1 = mailbox._addMessage('1', '1234567TCFGVYBH')
        msg2 = mailbox._addMessage('2', '1234567TCFGVZDdYBH')
        msg3 = mailbox._addMessage('3', '1234567TCFDZGVYBH')
        id = mailbox.getNextMessageUid()
        self.assertEquals(id, '4')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailFolderTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailfolder'),
        ))
