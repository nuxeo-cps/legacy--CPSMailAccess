#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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
from OFS.Image import File
from zope.publisher.browser import FileUpload
import unittest
from zope.testing import doctest
import sys
from Products.CPSMailAccess.interfaces import IMailBox, IMailFolder
from Products.CPSMailAccess.mailbox import MailBox, MailBoxParametersView
from basetestcase import MailTestCase
from Testing.ZopeTestCase import installProduct

from Products.CPSMailAccess import mailbox


installProduct('TextIndexNG2')

class FakeFieldStorage:
    file = None
    filename = ''
    headers = []


class MailBoxTestCase(MailTestCase):

    def test_base(self):
        # single instance
        ob = MailBox('mailbox')
        self.assertNotEquals(ob, None)

    def test_Interface(self):
        # single instance
        ob = self._getMailBox()
        ob = ob.__of__(self.portal)

        self.assertEquals(self.portal.INBOX, ob)

    def test_MailBoxParametersView(self):
        # testing MailBoxParametersView generators
        mailbox = MailBox('mailbox')
        view = MailBoxParametersView(mailbox, None)
        self.assertNotEquals(view, None)

        params = view._getParameters()
        self.assertNotEquals(params, [])

        params = view.renderParameters()
        self.assertNotEquals(params, '')

        params = view.renderParametersForm()
        self.assertNotEquals(params, '')

        params = view.renderAddParamForm()
        self.assertNotEquals(params, '')


    def test_clipboard(self):
        # test clipboard
        mailbox = MailBox('mailbox')
        action, ids = mailbox.getClipboard()
        self.assertEquals(action, None)
        self.assertEquals(ids, None)
        mailbox.fillClipboard('cut', ['msg1'])
        action, ids = mailbox.getClipboard()
        self.assertEquals(action, 'cut')
        self.assertEquals(ids, ['msg1'])
        mailbox.fillClipboard('copy', ['msg8', 'msg1'])
        action, ids = mailbox.getClipboard()
        self.assertEquals(action, 'copy')
        self.assertEquals(ids, ['msg8', 'msg1'])
        mailbox.clearClipboard()
        action, ids = mailbox.getClipboard()
        self.assertEquals(action, None)
        self.assertEquals(ids, None)

    ### fake imap pb
    def oldtest_saveEditorMessage(self):
        # tests that the editor message gets copied into drafts
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        drafts = inbox._addFolder('Drafts', 'INBOX.Drafts')
        msg = mailbox.getCurrentEditorMessage()
        mailbox.saveEditorMessage()

        messages = drafts.objectItems()
        self.assertEquals(len(messages), 1)
        message = messages[0][1]

        self.assertEquals(message.digest, msg.digest)

    def test_getIdentitites(self):
        # tests indentity
        mailbox = self._getMailBox()
        self.assert_(mailbox.getIdentitites(), 'tz@nuxeo.com')

    def test_draftcreate(self):
        # tests that draft, trash, and sent gets created if they don't exist
        mailbox = self._getMailBox()

    def test_treeviewcaching(self):

        mailbox = self._getMailBox()
        mailbox.setTreeViewCache('chet baker rulez')
        cached = mailbox.getTreeViewCache()
        self.assertEquals(cached, 'chet baker rulez')
        mailbox.clearTreeViewCache()
        cached = mailbox.getTreeViewCache()
        self.assertEquals(cached, None)

    def test_maileditorcaching(self):
        mailbox = self._getMailBox()
        msg = mailbox._addMessage('ok', 'ok')
        mailbox.setCurrentEditorMessage(msg)
        cached = mailbox.getCurrentEditorMessage()
        self.assertEquals(cached, msg)
        mailbox.clearEditorMessage()
        # getCurrentEditorMessage creates a message if it does not exists
        cached = mailbox.getCurrentEditorMessage()
        self.assertNotEquals(cached, None)
        self.assertNotEquals(cached, msg)

    def test_mailcache(self):
        pass

        """XXXX need to test msg caching
           XXXX with retrieval and invalidations
        """

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailbox'),
        ))
