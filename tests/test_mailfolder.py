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

installProduct('TextIndexNG2')

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
        ### ???
        """
        for element in folder_types:
            self.assertEquals(IMailFolder.providedBy(element), True)
        """

        no_type = ob.getMailMessages(False, False)

        self.assertEquals(len(no_type), 0)

    def test_getMailMessagesCount(self):
        # testing getMailMessagesCount with all combos
        mailbox = self._getMailBox()
        ob = mailbox._addFolder('MyFolder', 'MyFolder')

        for i in range(10):
            ob._addFolder('folder_'+str(i), 'folder_'+str(i))
            #self.assertEquals(IMailFolder.providedBy(ob), True)     ??????????????

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
        """ ??????
        for element in folder_types:
            self.assertEquals(IMailFolder.providedBy(element), True)
        """

        no_type = ob.getMailMessages(False, False, True)
        self.assertEquals(len(no_type), 0)


    def test_getMailMessagesCountRecursive(self):
        # testing getMailMessagesCount with all combos recursively
        mailbox = self._getMailBox()
        ob = mailbox._addFolder('MyFolder', 'MyFolder')

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
        mailbox = self._getMailBox()
        ob = mailbox._addFolder('MyFolder', 'MyFolder')
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
        mailbox = self._getMailBox()
        ob = mailbox._addFolder('MyFolder', 'MyFolder')
        self.assert_(ob.isEmpty())
        for i in range(10):
            ob._addFolder()
        self.assert_(not ob.isEmpty())

    def test_childFoldersCount(self):
        mailbox = self._getMailBox()
        ob = mailbox._addFolder('MyFolder', 'MyFolder')
        self.assertEquals(ob.childFoldersCount(), 0)
        for i in range(10):
            ob._addFolder()
        for i in range(10):
            ob._addMessage('ok'+str(i), 'ok'+str(i))
        self.assertEquals(ob.childFoldersCount(), 10)

    def test_renaming(self):
        mailbox = self._getMailBox()
        Todos = mailbox._addFolder('Todos', 'Todos')
        self.assertEquals(Todos.server_name, 'Todos')
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

    def test_folder_deleting(self):
        mailbox = self._getMailBox()
        Trash = mailbox._addFolder('Trash', 'Trash')
        Todos = mailbox._addFolder('Todosez', 'Todosez')
        res = Todos.delete()
        self.assertEquals(Todos.server_name, 'INBOX.Trash.Todosez')
        self.assert_(hasattr(mailbox.Trash, 'Todosez'))
        self.assertEquals(mailbox.Trash.Todosez.getMailFolder().id, 'Trash')
        Todos = mailbox._addFolder('Todosez', 'Todosez')
        res = Todos.delete()
        self.assertEquals(Todos.server_name, 'INBOX.Trash.Todosez_1')
        self.assert_(hasattr(mailbox.Trash, 'Todosez_1'))

    def test_delete_whole_branch(self):
        mailbox = self._getMailBox()
        INBOX = mailbox._addFolder('INBOX', 'INBOX')
        # trash folder will be created when needed

        ob = INBOX._addFolder('MyFolder', 'MyFolder')
        self.assertEquals(ob.childFoldersCount(), 0)
        for i in range(10):
            ob._addFolder()
        for i in range(10):
            ob._addMessage('ok'+str(i), 'ok'+str(i))

        ob.delete()
        mailbox.emptyTrashFolder()

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

    def test_synchronizeFolder(self):
        mailbox = self._getMailBox()
        mailbox._synchronizeFolder()


    def test_MoveMessage(self):
        mailbox = self._getMailBox()
        folder1 = mailbox._addFolder('folder1', 'INBOX')
        folder2 = mailbox._addFolder('folder2', 'INBOX2')

        msg = folder1._addMessage('1', 'DFRTGYHJUKL')
        msg.uid = '1'

        folder1.moveMessage('1', folder2)

        self.assert_(not hasattr(folder1, '.1'))
        self.assert_(hasattr(folder2, '.1'))
        self.assertEquals(getattr(folder2, '.1'), msg)


    def test_copyMessage(self):
        mailbox = self._getMailBox()
        folder1 = mailbox._addFolder('folder1', 'INBOX')
        folder2 = mailbox._addFolder('folder2', 'INBOX2')

        msg = folder1._addMessage('1', 'DFRTGYHJUKL')
        msg.uid = '1'
        msg.setHeader('Subject', 'yopla')

        folder1.copyMessage('1', folder2)

        self.assert_(hasattr(folder1, '.1'))
        self.assert_(hasattr(folder2, '.1'))
        msg2 = getattr(folder2, '.1')
        self.assertEquals(msg2.getHeader('Subject'), ['yopla'])
        self.assertEquals(msg2.getHeader('Subject'), msg.getHeader('Subject'))

    def test_MailFolderWithAccents(self):
        mailbox = self._getMailBox()
        folder1 = mailbox._addFolder('ééouéééouééé', 'ééouéééouééé')
        self.assertEquals(folder1.title, 'ééouéééouééé')


    def test_renametwice(self):
        mailbox = self._getMailBox()
        folder1 = mailbox._addFolder('folder1', 'folder1')
        folder1.rename('folder2')
        self.assertEquals(folder1.server_name, 'folder2')
        folder1.rename('folde')
        self.assertEquals(folder1.server_name, 'folde')

    def test_subcreation(self):

        mailbox = self._getMailBox()
        folder1 = mailbox._addFolder('folder1', 'folder1')
        folder11 = folder1._addFolder('folder11', 'folder1.folder11')
        folder111 = folder11._addFolder('folder111', 'folder1.folder11.folder111')

        self.assertEquals(folder1.depth(), 1)
        self.assertEquals(folder11.depth(), 2)
        self.assertEquals(folder111.depth(), 3)

        self.assert_(folder1.canCreateSubFolder())
        self.assert_(folder11.canCreateSubFolder())
        self.assert_(folder111.canCreateSubFolder())

        mailbox._connection_params['max_folder_depth'] = 3

        self.assert_(folder1.canCreateSubFolder())
        self.assert_(folder11.canCreateSubFolder())
        self.assert_(not folder111.canCreateSubFolder())






def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailFolderTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailfolder'),
        ))
