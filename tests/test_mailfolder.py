#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
#         Tarek Ziad� <tz@nuxeo.com>
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
from Products.CPSMailAccess.mailfolder import MailFolder, MailFolderView
from Products.CPSMailAccess.mailexceptions import MailContainerError
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailbox import MailBox
from Products.CPSMailAccess.interfaces import IMailFolder, IMailMessage

installProduct('FiveTest')
installProduct('Five')

class MailFolderTestCase(ZopeTestCase):
    msg_key = 0

    def msgKeyGen(self):
        result = 'msg_' + str(self.msg_key)
        self.msg_key += 1
        return result

    def getPhysicalPath(self):
        """ fake getPhysicalPath
        """
        return ('fake',)

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

    def test_MailFolderViewInstance(self):
        # testing mail folder view instanciation
        ob = MailFolder()
        view = MailFolderView(ob, None)
        self.assertNotEquals(view, None)

    def test_renderMailList(self):
        # testing mail folder view instanciation
        ob = MailFolder()
        view = MailFolderView(ob, None)
        rendered_list = view.renderMailList()

        # empty folder
        self.assertEquals(rendered_list, [])

        # 5 sub folders and 2 messages
        ob = self.test_getMailMessagesCountRecursive()

        # adding a fake physical path
        ob.getPhysicalPath = self.getPhysicalPath

        view = MailFolderView(ob, None)
        rendered_list = view.renderMailList()

        self.assertEquals(rendered_list[len(rendered_list)-1]['url'], '.msg_232/view')

    def test_TreeView(self):
        # testing treeview renderer
        ob = self.test_getMailMessagesCountRecursive()
        view = MailFolderView(ob, None)

        self.assertRaises(MailContainerError, view.renderTreeView)

        ob = MailBox('box')
        ob.getPhysicalPath = self.getPhysicalPath

        for i in range(5):
            sub_folder = ob._addFolder('folder_'+str(i))
            if i == 0:
                first_sub_folder = sub_folder

            # hack for tests
            sub_folder.getPhysicalPath = self.getPhysicalPath

            for y in range(4):
                sub_sub_folder = sub_folder._addFolder('folder_'+str(y))

        view = MailFolderView(ob, None)

        treeview = view.renderTreeView()

        self.assertEquals(len(treeview), 5)
        first = treeview[0]

        self.assertEquals(first['object'], first_sub_folder)

    def test_TreeViewCache(self):
        ob = MailBox('box')
        ob.getPhysicalPath = self.getPhysicalPath

        for i in range(5):
            sub_folder = ob._addFolder('folder_'+str(i))
            if i == 0:
                first_sub_folder = sub_folder

            # hack for tests
            sub_folder.getPhysicalPath = self.getPhysicalPath

            for y in range(4):
                sub_sub_folder = sub_folder._addFolder('folder_'+str(y))

        view = MailFolderView(ob, None)

        treeview = view.renderTreeView()

        self.assertEquals(len(treeview), 5)
        first = treeview[0]

        self.assertEquals(first['object'], first_sub_folder)

        self.assertNotEquals(ob.getTreeViewCache(), None)

        treeviewagain = view.renderTreeView()
        self.assertEquals(treeviewagain, treeview)

        ob._addFolder('folder_XXXX')

        self.assertEquals(ob.getTreeViewCache(), None)

        treeviewagain = view.renderTreeView()
        self.assertNotEquals(treeviewagain, treeview)


    def test_createShortTitle(self):
        # test createShortTitle
        view = MailFolderView(None, None)

        ob = MailFolder('ok', 'INBOX.Trash.ok')

        title = view.createShortTitle(ob)
        self.assertEquals(title, 'ok')

        ob = MailMessage('.message1')
        ob.title = '.message1'

        title = view.createShortTitle(ob)
        self.assertEquals(title, 'message1')



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailFolderTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailfolder'),
        ))
