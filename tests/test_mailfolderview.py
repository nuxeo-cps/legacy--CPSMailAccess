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

installProduct('TextIndexNG2')

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
        self.assertEquals(rendered_list, (0, []))

        # 5 sub folders and 2 messages
        ob = self.test_getMailMessagesCountRecursive()

        # adding a fake physical path
        ob.getPhysicalPath = self.getPhysicalPath

        view = MailFolderView(ob, None)
        rendered_list = view.renderMailList()[1]

        self.assertEquals(rendered_list[len(rendered_list)-1]['url'],
                          '.msg_213/view')

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
        view = view.__of__(ob)

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
        view.rename('bolo')
        self.assertEquals(ob.title, 'bolo')
        self.assertEquals(ob.id, 'bolo')

    def test_renametwice(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX.ok')
        self.assertNotEqual(ob.getMailBox(), None)
        view = MailFolderView(ob, None)
        view = view.__of__(ob)

        res = view.rename('bolo')
        self.assertEquals(ob.title, 'bolo')
        self.assertEquals(ob.id, 'bolo')
        self.assertEquals(res, ob)

        res = view.rename('bol')
        self.assertEquals(ob.title, 'bol')
        self.assertEquals(ob.id, 'bol')
        self.assertEquals(res, ob)

    def test_renamemaxsize(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX.ok')
        self.assertNotEqual(ob.getMailBox(), None)
        view = MailFolderView(ob, None)
        view = view.__of__(ob)
        view.rename('boloyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
        self.assertEquals(ob.title, 'boloyyyyyyyyyyyyyyyy')
        self.assertEquals(ob.id, 'boloyyyyyyyyyyyyyyyy')

    def test_rename2times(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX.ok')
        self.assertNotEqual(ob.getMailBox(), None)
        view = MailFolderView(ob, None)
        view = view.__of__(ob)
        view.rename('boloyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
        self.assertEquals(ob.title, 'boloyyyyyyyyyyyyyyyy')
        self.assertEquals(ob.id, 'boloyyyyyyyyyyyyyyyy')
        view.rename('bolod')
        self.assertEquals(ob.title, 'bolod')
        self.assertEquals(ob.id, 'bolod')

    def test_manageContent_copy(self):
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

    def test_manageContent_cut(self):
        # test content manipulations
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX')
        self.assertEqual(ob.getMailBox(), box)
        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)
        self.assertEquals(view.context.getMailBox(), box)
        kw = {'msg_1': 'on', 'msg_2': 'on'}
        view.manageContent(action='cut', **kw)
        self.assertEquals(box.getClipboard(),('cut', ['INBOX.2', 'INBOX.1']))
        self.assert_(not view.clipBoardEmpty())

    def test_manageContent_clear_clipboard_empty_and_count(self):
        # test content manipulations
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX')
        self.assertEqual(ob.getMailBox(), box)
        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)
        self.assertEquals(view.context.getMailBox(), box)
        kw = {'msg_1': 'on', 'msg_2': 'on'}

        view.manageContent(action='cut', **kw)
        self.assertEquals(box.getClipboard(),('cut', ['INBOX.2', 'INBOX.1']))
        self.assert_(view.clipBoardCount()==2)

        view.manageContent(action='clear')
        self.assertEquals(box.getClipboard(),(None, None))
        self.assert_(view.clipBoardEmpty())
        self.assert_(view.clipBoardCount()==0)

    def test_manageContent_cut_paste(self):
        # test content manipulations
        box = self._getMailBox()

        ob2 = box._addFolder('INBOX2', 'INBOX2')
        view2 = MailFolderView(ob2, self.request)
        view2 = view2.__of__(ob2)

        ob = box._addFolder('INBOX', 'INBOX')
        ob._addMessage('1', '1')
        ob._addMessage('2', '2')
        ob._addMessage('3', '3')

        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)

        # cut
        kw = {'msg_1': 'on', 'msg_2': 'on'}
        view.manageContent(action='cut', **kw)
        self.assertEquals(box.getClipboard(),('cut', ['INBOX.2', 'INBOX.1']))

        # paste
        view2.manageContent(action='paste', **kw)

        self.assertEquals(len(ob2.objectIds()), 2)
        self.assertEquals(len(ob.objectIds()), 1)

    def test_manageContent_copy_paste(self):
        # test content manipulations
        box = self._getMailBox()

        ob2 = box._addFolder('INBOX2', 'INBOX2')
        view2 = MailFolderView(ob2, self.request)
        view2 = view2.__of__(ob2)

        ob = box._addFolder('INBOX', 'INBOX')
        ob._addMessage('1', '1')
        ob._addMessage('2', '2')
        ob._addMessage('3', '3')

        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)

        # cut
        kw = {'msg_1': 'on', 'msg_2': 'on'}
        view.manageContent(action='copy', **kw)
        self.assertEquals(box.getClipboard(),('copy', ['INBOX.2', 'INBOX.1']))

        # paste
        view2.manageContent(action='paste', **kw)

        self.assertEquals(len(ob2.objectIds()), 2)
        self.assertEquals(len(ob.objectIds()), 3)


    def test_manageContent_delete(self):
        # test content manipulations
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX')
        ob._addFolder('Trash', 'Trash')

        ob._addMessage('1', '1')
        ob._addMessage('2', '2')
        ob._addMessage('3', '3')

        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)

        # DELETE
        kw = {'msg_1': 'on', 'msg_2': 'on'}
        view.manageContent(action='delete', **kw)

        self.assertEquals(len(ob.objectIds()), 2)


    def test_getMaxFolderSize(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX')
        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)
        mfs = view.getMaxFolderSize()
        self.assertEquals(mfs, 20)

    def test_getMsgIconName(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX')
        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)

        message = box._addMessage('msg', 'msg')

        message.read = 0
        icon = view.getMsgIconName(message)
        self.assertEquals(icon, 'cpsma_message_new.png')

        message.deleted = 1
        icon = view.getMsgIconName(message)
        self.assertEquals(icon, 'cpsma_mini_mail_delete.png')

    def test_getMessageUidAndFolder(self):
        box = self._getMailBox()
        ob = box._addFolder('INBOX', 'INBOX')
        view = MailFolderView(ob, self.request)
        view = view.__of__(ob)

        message = box._addMessage('msg', 'msg')

        res = view.getMessageUidAndFolder('INBOX.msg')
        self.assertEquals(res, (ob, 'msg'))

        res = view.getMessageUidAndFolder('INBOX.mdzsg')
        self.assertEquals(res, (ob, None))

        res = view.getMessageUidAndFolder('INadzadzBOX.mdzsg')
        self.assertEquals(res, (None, None))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailFolderViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailfolderview'),
        ))
