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
from Products.CPSMailAccess.mailfolderview import MailFolderView
from Products.CPSMailAccess.mailexceptions import MailContainerError
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailbox import MailBox
from Products.CPSMailAccess.interfaces import IMailFolder, IMailMessage
from basetestcase import MailTestCase

class MailFolderViewTestCase(MailTestCase):

    def test_getMailMessagesCountRecursive(self):
        # testing getMailMessagesCount with all combos recursively
        box = self._getMailBox()

        ob = box._addFolder('folder', 'folder')

        for i in range(10):
            folder = ob._addFolder('folder_'+str(i), 'folder_'+str(i))
            key = self.msgKeyGen()
            msg = folder._addMessage(key,key)
            msg.addHeader('From', 'Me')
            msg.addHeader('To', 'You')
            msg.addHeader('Date', 'Now')
            for y in range(2):
                subfolder = folder._addFolder()
                for y in range(5):
                    key = self.msgKeyGen()
                    msg = subfolder._addMessage(key, key)
                    msg.addHeader('From', 'Me')
                    msg.addHeader('To', 'You')
                    msg.addHeader('Date', 'Now')

        for i in range(123):
            key = self.msgKeyGen()
            msg = ob._addMessage(key, key)
            msg.addHeader('From', 'Me')
            msg.addHeader('To', 'You')
            msg.addHeader('Date', 'Now')

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

        # testing a message
        msg_entry = rendered_list[0]
        self.assertEquals(msg_entry['From'], 'Me')
        #self.assertEquals(msg_entry['To'], 'You')
        #self.assertEquals(msg_entry['Date'], 'Now')


    def test_TreeView(self):
        # testing treeview renderer
        ob = self.test_getMailMessagesCountRecursive()
        view = MailFolderView(ob, None)
        view = view.__of__(ob)

        #self.assertRaises(MailContainerError, view.renderTreeView)

        ob = self._getMailBox()
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
        view = view.__of__(ob)

        treeview = view.renderTreeView()

        self.assertEquals(len(treeview), 5)
        first = treeview[0]

        self.assertEquals(first['object'], first_sub_folder)

    def test_TreeViewCache(self):
        ob = self._getMailBox()
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

    def test_addFolder(self):
        # test createShortTitle
        box = self._getMailBox()
        ob = box._addFolder('ok', 'ok')
        view = MailFolderView(ob, None)
        view = view.__of__(ob)
        view.addFolder('sub')
        self.assert_(hasattr(ob, 'sub'))

    def test_rename(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX.ok')
        self.assertNotEqual(ob.getMailBox(), None)
        view = MailFolderView(ob, None)
        view = view.__of__(ob)
        view.rename('bolo', False)
        self.assertEquals(ob.title, 'bolo')
        self.assertEquals(ob.id, 'bolo')

    def test_renamemaxsize(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX.ok')
        self.assertNotEqual(ob.getMailBox(), None)
        view = MailFolderView(ob, None)
        view = view.__of__(ob)
        view.rename('boloyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', False)
        self.assertEquals(ob.title, 'boloyyyyyyyyyyyyyyyy')
        self.assertEquals(ob.id, 'boloyyyyyyyyyyyyyyyy')

    def test_rename2times(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX.ok')
        self.assertNotEqual(ob.getMailBox(), None)
        view = MailFolderView(ob, None)
        view = view.__of__(ob)
        view.rename('boloyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', False)
        self.assertEquals(ob.title, 'boloyyyyyyyyyyyyyyyy')
        self.assertEquals(ob.id, 'boloyyyyyyyyyyyyyyyy')
        view.rename('bolod', False)
        self.assertEquals(ob.title, 'bolod')
        self.assertEquals(ob.id, 'bolod')

    def test_manageContent(self):
        # test content manipulations
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX')
        self.assertEqual(ob.getMailBox(), box)
        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)
        self.assertEquals(view.context.getMailBox(), box)
        kw = {'msg_1': 'on', 'msg_2': 'on'}
        view.manageContent(action='copy', **kw)
        self.assertEquals(box.getClipboard(),('copy', ['INBOX.2', 'INBOX.1']))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailFolderViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailfolderview'),
        ))
