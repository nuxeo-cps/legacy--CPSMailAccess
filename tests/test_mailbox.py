#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
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
        mailbox = self._getMailBox()
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
        mailbox = self._getMailBox()
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
        self.assertEquals(cached.getRawMessage(), msg.getRawMessage())
        mailbox.clearEditorMessage()
        # getCurrentEditorMessage creates a message if it does not exists
        cached = mailbox.getCurrentEditorMessage()
        self.assertNotEquals(cached, None)
        self.assertNotEquals(cached.getRawMessage(), msg.getRawMessage())

    def test_mailcache(self):
        mailbox = self._getMailBox()
        mailbox.clearMailCache()
        msg = mailbox._addMessage('ok', 'ok')
        mailbox.addMailToCache(msg, 'zeMail')

        mailbox.addMailToCache(msg, 'zeMail')

        cache = mailbox.getMailFromCache('zeMail', False)
        self.assertEquals(cache, msg)

        cache = mailbox.getMailFromCache('zeMail')
        self.assertEquals(cache, msg)
        self.assertEquals(mailbox.getMailFromCache('zeMail'), None)


    def test_createMailDirectoryEntry(self):
        mailbox = self._getMailBox()

        res = mailbox._createMailDirectoryEntry('Tarek Ziadé <tarek@ziade.org>')
        self.assertEquals(res, {'mails_sent': 0, 'id': u'tarekziade.org', 'fullname':
            u'Tarek Ziad\xe9', 'email': u'tarek@ziade.org', 'givenName':
            u'Tarek', 'email': u'tarek@ziade.org', 'sn': u'Ziad\xe9'})

        res = mailbox._createMailDirectoryEntry('Tarek <tarek@nuxeo.com>')
        self.assertEquals(res, {'mails_sent': 0, 'fullname': u'Tarek',
                                'givenName': u'Tarek',
                                'email': 'tarek@nuxeo.com', 'id':
                                'tareknuxeo.com'})

        res = mailbox._createMailDirectoryEntry('tz@nuxeo.com>')
        self.assertEquals(res, {'mails_sent': 0,'fullname': u'',
                                'email': 'tz@nuxeo.com',
                                'id': 'tznuxeo.com'})

    def test_readDirectoryValue(self):

        mailbox = self._getMailBox()
        res = mailbox.readDirectoryValue('members', 'tziade', ['fullname'])
        self.assert_(isinstance(results, dict))

    def test_readDirectoryValue(self):

        mailbox = self._getMailBox()
        res = mailbox.getIdentitites()
        self.assertEquals(res, [{'fullname': 'Tarek Ziad\xe9',
                                 'email': 'tz@nuxeo.com'}])

    def test_directoryToParam(self):
        mailbox = self._getMailBox()

        res = mailbox._directoryToParam('${members.webmail_login}')
        self.assertEquals(res, 'tziade')

        res = mailbox._directoryToParam('${members.webmail_password}')
        self.assertEquals(res, 'do_not_reveal_it_please')

        res = mailbox._directoryToParam('nothing')
        self.assertEquals(res, 'nothing')

    def test_elementIsInTrash(self):
        mailbox = self._getMailBox()
        Trash = mailbox._addFolder('Trash', 'INBOX.Trash')
        Todos = mailbox._addFolder('Todosez', 'INBOX.Todosez')
        self.assert_(not mailbox.elementIsInTrash(Todos))

        res = Todos.delete()
        self.assert_(mailbox.elementIsInTrash(Todos))

    def test_generateZemanticCat(self):
        mailbox = self._getMailBox()
        mb = mailbox._getZemanticCatalog()
        self.assert_(mb is not None)

    def test_checkIndexStack(self):
        #checks that index stack gets filled
        mailbox = self._getMailBox()
        indexStack = []
        mailbox._syncdirs([{'Name' : 'INBOX'}], True, indexStack)
        self.assertEquals(len(indexStack), 1)

        indexStack = []
        mailbox._syncdirs([{'Name' : 'INBOX'}, {'Name' : 'INBOX.Trash'}], True, indexStack)
        self.assertEquals(len(indexStack), 2)

    def test_synchronize(self):
        mailbox = self._getMailBox()
        logs = mailbox.synchronize()
        self.assert_(len(logs)>100)



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailbox'),
        ))
