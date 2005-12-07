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
import unittest
import sys
import time

from OFS.Folder import Folder
from OFS.Image import File
from Testing.ZopeTestCase import installProduct

from zope.publisher.browser import FileUpload
from zope.testing import doctest

from Products.CPSMailAccess.interfaces import IMailBox, IMailFolder
from Products.CPSMailAccess.mailbox import MailBox, MailFolderTicking
import Products.CPSMailAccess.mailbox as mailbox
from basetestcase import MailTestCase

from Products.CPSMailAccess import mailbox

class FakeDirectory(Folder):
    id_field = 'i am the id field'

class FakeDirectoryTool(Folder):

    members = FakeDirectory()
    addressbook = FakeDirectory()

    def listVisibleDirectories(self):
        return ['members', 'roles', 'groups', 'addressbook']

    def searchEntries(self, return_fields, **kw):

        return [('tarek', {'id': 'tarek', 'fullname' : 'Tarek Ziadé',
                 'email' : 'tz@nuxeo.com', 'mails_sent' : 32})]

    def _searchEntries(self, directory_name, return_fields=None, **kw):
        """ search for entries """
        return [('tarek', {'id': 'tarek', 'fullname' : 'Tarek Ziadé',
                 'email' : 'tz@nuxeo.com', 'mails_sent' : 32})]

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

    def test_saveEditorMessage(self):
        # tests that the editor message gets copied into drafts
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        drafts = inbox._addFolder('Drafts', 'INBOX.Drafts')
        msg = mailbox.getCurrentEditorMessage()
        self.assertEquals(msg.draft, 0)

        mailbox.saveEditorMessage()

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
        cached.uid = msg.uid    # uid is not copied
        self.assertEquals(cached.getHeader('Message-ID'),
                          msg.getHeader('Message-ID'))

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

        res = mailbox._createMailDirectoryEntry('paf')
        self.assertEquals(res, None)


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
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        Trash = inbox._addFolder('Trash', 'INBOX.Trash')
        Todos = inbox._addFolder('Todosez', 'INBOX.Todosez')

        self.assert_(not mailbox.elementIsInTrash(Todos))

        res = Todos.delete()
        self.assert_(mailbox.elementIsInTrash(Todos))

    def test_generateZemanticCat(self):
        mailbox = self._getMailBox()
        mb = mailbox._getZemanticCatalog()
        self.assert_(mb is not None)

    def test_checkIndexStack(self):
        # checks that index stack gets filled
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        indexStack = []
        mailbox._syncdirs([{'Name' : 'INBOX'}], True, indexStack)
        self.assertEquals(len(indexStack), 1)

    def test_checkIndexStack2(self):
        mailbox = self._getMailBox()
        indexStack = []
        mailbox.INBOX._addFolder('Trash', 'INBOX.Trash')
        mailbox._syncdirs([{'Name' : 'INBOX'}, {'Name' : 'INBOX.Trash'}], True, indexStack)
        self.assertEquals(len(indexStack), 2)

    def test_synchronize(self):
        mailbox = self._getMailBox()
        logs = mailbox.synchronize()
        self.assert_(len(logs)>30)

    def test_searchUsers(self):
        self.portal.portal_directory = FakeDirectoryTool()
        portal_dir = self.portal.portal_directory
        mailbox = self._getMailBox()
        mailbox._searchEntries = portal_dir._searchEntries

        results = mailbox.searchDirectoryEntries('tarek')
        self.assertEquals(len(results), 2)

        results = mailbox.searchDirectoryEntries('tarek@nuxeo.com')
        self.assertEquals(len(results), 2)

        results = mailbox.searchDirectoryEntries('tarek z')
        self.assertEquals(len(results), 2)

    def test_moveElement(self):
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')

        # the user can move a message to another folder
        # msg_INBOX__950   to_folder_INBOX
        # msg_INBOX.CVS__950   to_folder_INBOX.LOGS
        folder1 =  inbox._addFolder('folder1', 'INBOX.folder1')
        folder1._addMessage('.1', 'message1')

        self.assertEquals(list(folder1.objectIds()), ['.1'])

        folder2 =  inbox._addFolder('folder2', 'INBOX.folder2')

        target = mailbox.moveElement('msg_INBOX.folder1__.1',
                                     'to_folder_INBOX.folder2')

        self.assertEquals(target, folder1)

        self.assertEquals(list(folder1.objectIds()), [])
        self.assertEquals(list(folder2.objectIds()), ['.1'])

        # make sure a message that moves where it is already
        # does not do anything
        target = mailbox.moveElement('msg_INBOX.folder2__.1',
                                     'to_folder_INBOX.folder2')

        self.assertEquals(target, None)

        # the user can move folder into another folder
        # from_folder_INBOX.CVS  to_folder_INBOX.LOGS

        # cannot move a folder into its subfolder or descendant
        folder11 =  folder1._addFolder('folder11', 'INBOX.folder1.folder11')
        target = mailbox.moveElement('from_folder_INBOX',
                                     'to_folder_INBOX.folder1')
        self.assertEquals(target, None)

        target = mailbox.moveElement('from_folder_INBOX',
                                     'to_folder_INBOX.folder1.folder11')
        self.assertEquals(target, None)

        # moving folder 2 into folder 1
        self.assertEquals(len(inbox.objectIds()), 2)
        self.assertEquals(folder2.getMailFolder(), inbox)
        self.assertEquals(len(folder1.objectIds()), 1)

        target = mailbox.moveElement('from_folder_INBOX.folder2',
                                     'to_folder_INBOX.folder1')

        self.assertEquals(target, inbox)

        self.assertEquals(len(folder1.objectIds()), 2)
        self.assertEquals(len(inbox.objectIds()), 1)
        folder2 = getattr(folder1, 'folder2')
        self.assertEquals(folder2.getMailFolder(), folder1)
        self.assertEquals(folder2.server_name, 'INBOX.folder1.folder2')

    def test_moveElementWithReadOnly(self):
        # make sure the user can't drag'n'drop in read-only folder
        mailbox = self._getMailBox()
        portal_webmail = self.portal.portal_webmail
        portal_webmail.default_connection_params['protected_folders'] = ('', 1)
        portal_webmail.default_connection_params['read_only_folders'] = \
            ('INBOX.Sent', 1)
        mailbox._connection_params['protected_folders'] = ('', 1)
        mailbox._connection_params['read_only_folders'] = \
            ('INBOX.Sent', 1)
        inbox = mailbox._addFolder('INBOX', 'INBOX')

        # the user can move a message to another folder
        # msg_INBOX__950   to_folder_INBOX
        # msg_INBOX.CVS__950   to_folder_INBOX.LOGS
        folder1 =  inbox._addFolder('folder1', 'INBOX.folder1')
        folder1._addMessage('.1', 'message1')

        self.assertEquals(list(folder1.objectIds()), ['.1'])

        folder2 =  inbox._addFolder('Sent', 'INBOX.Sent')

        target = mailbox.moveElement('msg_INBOX.folder1__.1',
                                     'to_folder_INBOX.Sent')

        self.assertEquals(target, None)



    def test_ticking(self):
        folder = MailFolderTicking('ok', 'ok')
        self.assert_(not folder.isSynchronizing())
        mailbox._idle_time = 1
        folder.synchroTick()
        self.assert_(folder.isSynchronizing())
        time.sleep(2)
        self.assert_(not folder.isSynchronizing())
        folder.synchroTick()
        self.assert_(folder.isSynchronizing())
        folder.clearSynchro()
        self.assert_(not folder.isSynchronizing())

    def test_ticking2(self):
        folder = MailFolderTicking('ok', 'ok')
        self.assert_(not folder.isSynchronizing(1))
        mailbox._idle_time = 1
        folder.synchroTick(1)
        self.assert_(folder.isSynchronizing(1))
        time.sleep(2)
        self.assert_(not folder.isSynchronizing(1))
        folder.synchroTick(1)
        self.assert_(folder.isSynchronizing(1))
        folder.clearSynchro(1)
        self.assert_(not folder.isSynchronizing(1))

    def test_filterapis(self):
        mailbox = self._getMailBox()
        filters = mailbox.getFilters()
        self.assert_(not mailbox.hasFilters())
        filters.addFilter('do', 're', 'mi', 'fa', 'sol')
        self.assert_(mailbox.hasFilters())

    def test_clearMailBodies(self):
        mailbox = self._getMailBox()
        folder1 =  mailbox._addFolder('folder1', 'INBOX.folder1')
        mail = mailbox._addMessage('.1', 'message1')
        mail._getStore()._payload = 'go'
        mail._file_list = ['ok']
        mailbox.clearMailBodies()
        self.assertEquals(mail._getStore()._payload, '')
        self.assertEquals(mail._file_list, [])

    def test_searchInConnection(self):
        mailbox = self._getMailBox()
        res= mailbox.searchInConnection('(body test)')
        self.assert_(len(res) > 0)

    def test_getPublicAdressBookName(self):
        mailbox = self._getMailBox()
        self.assertEquals(mailbox.getPublicAdressBookName(), 'addressbook')

    def test_indexMails(self):
        mailbox = self._getMailBox()
        # simple calls
        mailbox.indexMails([])
        mailbox.indexMails([], background=True)

        # try to call it asynced
        from Products.CPSMailAccess import mailbox as box_module
        box_module.can_async = True

    def test_indexMails2(self):
        # check if the indexer is bullet proof when
        # zasync is not properly configured
        mailbox = self._getMailBox()
        def _canAsync(ob):
            return True

        def _asyncedCall(*args, **kw):
            raise AttributeError

        import Products.CPSMailAccess.mailbox as box_module
        box_module.canAsync = _canAsync
        box_module.asyncedCall = _asyncedCall

        mailbox.indexMails([], background=True)

    def test_directoryToParam2(self):
        # sometimes, we get more than
        # one entry for specific directories, like ldapdirs
        def _searchEntries(*args, **kw):
            return [(1, {'id': '_xx'}), (2, {'id': '_xxx'})]

        def _getDirectoryIdField(*args, **kw):
            return 'id'

        mailbox = self._getMailBox()
        mailbox.id = 'box__xx'
        mailbox._getDirectoryIdField = _getDirectoryIdField
        mailbox._searchEntries = _searchEntries
        res = mailbox._directoryToParam('${directory.id}')
        self.assertEquals(res, '_xx')

    def test_failedCopyToSend(self):

        class FakeMailer:
            def send(*arg, **kw):
                return True, 'OK'

        def _writeMsg(*arg, **kw):
            return ''

        def _getMailDeliverer(*arg, **kw):
            return FakeMailer()

        mailbox = self._getMailBox()
        mailbox.id = 'box__xx'
        mailbox._getconnector().writeMessage = _writeMsg

        old_getMailDeliverer = self.portal.portal_webmail.getMailDeliverer
        try:
            self.portal.portal_webmail.getMailDeliverer = _getMailDeliverer
            ob = self.getMailInstance(6)

            mailbox.sendNotification('me', ob)
            mailbox.sendEditorsMessage()
            mailbox.saveEditorMessage()
        finally:
            self.portal.portal_webmail.getMailDeliverer = old_getMailDeliverer

    def test_Interface(self):
        # make sure the contract is respected
        from Interface.Verify import verifyClass
        self.failUnless(verifyClass(IMailBox, MailBox))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailbox'),
        ))
