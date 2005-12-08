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

def openfile(filename, mode='r'):
    path = os.path.join(os.path.dirname(landmark), 'data', filename)
    return open(path, mode)

def testGetNextMessageUid(self):
    msgs = self.getMailMessages(False, True, False)
    highest_id = 0
    for msg in msgs:
        uid = int(msg.uid)
        if uid > highest_id:
            highest_id = uid
    return str(highest_id + 1)

from mailbox import MailBox
MailFolder.getNextMessageUid = testGetNextMessageUid


class MailFolderTestCase(MailTestCase):

    def test_title_or_id(self):
        mailbox = self._getMailBox()
        self.assertEquals(mailbox.title_or_id(), mailbox.id)

        folder = mailbox._addFolder('mbox')
        self.assertEquals(folder.title_or_id(), 'mbox')

        inbox = mailbox._addFolder('INBOX')
        self.assertEquals(inbox.title_or_id(), 'translated:INBOX')

        folder = inbox._addFolder('Drafts', 'INBOX.Drafts')
        self.assertEquals(folder.title_or_id(), 'translated:Drafts')

    def test_getMailBox(self):
        mailbox = self._getMailBox()
        mailbox._addFolder('folder')
        folder = mailbox.folder
        self.assertEquals(folder.getMailBox(), mailbox)

    def test_getMailBox2(self):
        mailbox = self._getMailBox()
        mailbox._addFolder('folder')
        o = self
        folder = mailbox.folder
        self.myfolder = folder
        self.assertEquals(self.myfolder.getMailBox(), mailbox)

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

    def test_getMailMessages2(self):
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        folder1 = inbox._addFolder('folder1', 'INBOX.folder1')
        folder2 = inbox._addFolder('folder2', 'INBOX.folder2')

        sub_folders = mailbox.getMailMessages(list_folder=True,
                                              list_messages=False,
                                              recursive=True)
        self.assertEquals(len(sub_folders), 3)

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

    def test_renaming2(self):
        # controls the depth
        mailbox = self._getMailBox()
        Todos = mailbox._addFolder('Todos', 'Todos')
        self.assertEquals(Todos.server_name, 'Todos')
        res = Todos.rename('INBOX.Foo.Bar')
        self.assert_(not res)

    def test_simpleFolderName(self):
        mailbox = self._getMailBox()
        ob = MailFolder('Todos')
        mailbox._setObject('Todos', ob)
        ob = mailbox.Todos
        ob.server_name = 'INBOX.Todos'
        self.assertEquals(ob.simpleFolderName(), 'Todos')

    def test_folder_deleting(self):
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'Trash')
        Trash = inbox._addFolder('Trash', 'INBOX.Trash')
        Todos = inbox._addFolder('Todosez', 'INBOX.Todosez')
        res = Todos.delete()
        self.assertEquals(Todos.server_name, 'INBOX.Trash.Todosez')
        self.assert_(inbox.Trash.has_key('Todosez'))
        self.assertEquals(inbox.Trash.Todosez.getMailFolder().id, 'Trash')
        Todos = mailbox._addFolder('Todosez', 'Todosez')
        res = Todos.delete()
        self.assertEquals(Todos.server_name, 'INBOX.Trash.Todosez_1')
        self.assert_(inbox.Trash.has_key('Todosez_1'))

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
        msg1 = mailbox.moveMessage(msg1.uid, Trash)
        self.assert_('.1' in list(Trash.objectIds()))
        self.assert_('.1' not in list(mailbox.objectIds()))

    def test_message_moving_with_IMAP(self):
        mailbox = self._getMailBox()
        msg1 = mailbox._addMessage('1', '1234567TCFGVYBH')
        self.assertEquals(msg1.getMailFolder(), mailbox)
        Trash = mailbox._addFolder('Trash')
        self.assertEquals(list(Trash.objectIds()), [])
        self.assertEquals(list(mailbox.objectIds()), ['.1', 'Trash'])
        mailbox.moveMessage(msg1.uid, Trash)
        self.assertEquals(list(mailbox.objectIds()), ['Trash'])
        self.assertEquals(list(Trash.objectIds()), ['.1'])

    def test_id_generator(self):
        mailbox = self._getMailBox()
        msg1 = mailbox._addMessage('1', '1')
        msg2 = mailbox._addMessage('2', '2')
        msg3 = mailbox._addMessage('3', '3')
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

        self.assertEquals(mailbox._connection_params['max_folder_depth'],
                          (0, 0))

        self.assertEquals(mailbox.getConnectionParams()['max_folder_depth'], 0)


        self.assertEquals(folder1.depth(), 1)
        self.assertEquals(folder11.depth(), 2)
        self.assertEquals(folder111.depth(), 3)

        self.assert_(folder1.canCreateSubFolder())
        self.assert_(folder11.canCreateSubFolder())
        self.assert_(folder111.canCreateSubFolder())

        mailbox._connection_params['max_folder_depth'] = (3, 0)

        self.assert_(folder1.canCreateSubFolder())
        self.assert_(folder11.canCreateSubFolder())
        self.assert_(not folder111.canCreateSubFolder())

    def test_caching(self):
        # testing caches
        mailbox = self._getMailBox()

        folder1 = mailbox._addFolder('folder1', 'folder1')
        cached = folder1.getMailListFromCache(1, 787, 'yo', True)
        self.assertEquals(cached, None)

        folder1.addMailListToCache('data', 1, 787, 'yo', True)
        folder1.addMailListToCache('more data', 3, 387, 'yo', True)
        folder1.addMailListToCache('dadddta', 1, 383, 'yo', True)

        cached = folder1.getMailListFromCache(1, 787, 'yo', True)
        self.assertEquals(cached, 'data')

        cached = folder1.getMailListFromCache(3, 387, 'yo', True)
        self.assertEquals(cached, 'more data')

        self.assertEquals((3, 387, 'yo', True),
                          folder1.getLastMailListSortCache())

        cached = folder1.getMailListFromCache(1, 383, 'yo', True)
        self.assertEquals(cached, 'dadddta')
        self.assertEquals((1, 383, 'yo', True),
                          folder1.getLastMailListSortCache())

        infos = folder1.getLastMailListSortCache()
        self.assertEquals(infos, (1, 383, 'yo', True))

    def test_runFilters(self):

        mailbox = self._getMailBox()
        filter_engine = mailbox.getFilters()

        # labels with [COOL] some messages
        filter_engine.addFilter('Subject', 1, 'cool', 3, 'COOL')

        folder1 = mailbox._addFolder('folder1', 'folder1')

        for i in range(5):
            key = self.msgKeyGen()
            msg = folder1._addMessage(key, key)
            msg.setHeader('Subject', 'banal subject')

        for i in range(5):
            key = self.msgKeyGen()
            msg = folder1._addMessage(key, key)
            msg.setHeader('Subject', 'pretty cool subject')

        # checkink post state
        msgs = folder1.getMailMessages(list_folder=False,
                                       list_messages=True, recursive=False)

        for msg in msgs:
            subject = msg.getHeader('Subject')
            subject = subject[0]
            self.assert_(subject in ('banal subject',
                                          'pretty cool subject'))

        folder1.runFilters()

        # checkink result
        msgs = folder1.getMailMessages(list_folder=False,
                                       list_messages=True, recursive=False)

        for msg in msgs:
            subject = msg.getHeader('Subject')
            subject = subject[0]
            self.assert_(subject in ('banal subject',
                                          '[COOL] pretty cool subject'))

    def test_rename_weirdo(self):
        mailbox = self._getMailBox()
        Todos = mailbox._addFolder('Todos', 'Todos')
        self.assertEquals(Todos.server_name, 'Todos')
        self.assertEquals(Todos.title, 'Todos')

        res = Todos.rename('[Todos]')
        self.assertEquals(Todos.server_name, '[Todos]')
        self.assertEquals(Todos.title, '[Todos]')

        res = Todos.rename('[Todééé $zéee"r"eé^os]')
        self.assertEquals(Todos.server_name, '[Todééé $zéee"r"eé^os]')
        self.assertEquals(Todos.title, '[Todééé $zéee"r"eé^os]')

    def test_createSubBlocs(self):
        mailbox = self._getMailBox()
        uids = []
        for i in range(421):
            uids.append(str(i))

        blocs = mailbox._createSubBlocs(uids, 200)

        self.assertEquals(len(blocs), 3)
        self.assertEquals(len(blocs[0]), 200)
        subs = []
        for i in range(200):
            subs.append(str(i))
        self.assertEquals(blocs[0], subs)

        self.assertEquals(len(blocs[1]), 200)
        subs = []
        for i in range(200):
            subs.append(str(i+200))
        self.assertEquals(blocs[1], subs)

        self.assertEquals(len(blocs[2]), 21)
        subs = []
        for i in range(21):
            subs.append(str(i+400))
        self.assertEquals(blocs[2], subs)

    def test_nextId(self):
        mailbox = self._getMailBox()
        folder = mailbox._addFolder('MyFolder', 'MyFolder')
        id = mailbox._nextId('.10')
        self.assertEquals(id, '.11')

    def test_getUidFromId(self):
        mailbox = self._getMailBox()
        folder = mailbox._addFolder('MyFolder', 'MyFolder')
        id = folder.getUidFromId('.2')
        self.assertEquals(id, '2')
        id = folder.getUidFromId('.10')
        self.assertEquals(id, '10')

    def test_getFlaggedMessageList(self):
        mailbox = self._getMailBox()
        folder = mailbox._addFolder('MyFolder', 'MyFolder')

        for i in range(50):
            key = '.'+str(i)
            msg = folder._addMessage(key, key)
            if i > 25:
                msg.seen = 0
            else:
                msg.seen = 1
            if i < 10:
                msg.junk = 1
            else:
                msg.junk = 0

        res = folder.getFlaggedMessageCount(['seendzdz', 'junk'])
        self.assertEquals(res, 0)

        res = folder.getFlaggedMessageCount(['seen', 'junk'])
        self.assertEquals(res, 10)

        res = folder.getFlaggedMessageCount(['seen'])
        self.assertEquals(res, 26)

        res = folder.getFlaggedMessageCount(['-seen'])
        self.assertEquals(res, 24)

        res = folder.getFlaggedMessageCount(['junk'])
        self.assertEquals(res, 10)

        res = folder.getFlaggedMessageCount(['-seen', 'junk'])
        self.assertEquals(res, 0)

    def test_add_and_del(self):
        # check that deletemessage works
        mailbox = self._getMailBox()
        mailbox._addMessage('.1', 'xxx')
        mailbox._deleteMessage('.1')
        mailbox._addMessage('.1', 'xxx')

    def test_rename_with_spaces(self):
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        folder1 = inbox._addFolder('with space', 'INBOX.with space')
        folder2 = inbox._addFolder('folder2', 'INBOX.folder2')
        folder2.rename('INBOX.with space.folder2', True)
        self.assertEquals(folder1['folder2'], folder2)

    def test_isReadOnlyProtections(self):
        box = self._getMailBox()
        box._connection_params['protected_folders'] = ('', 1)
        box._connection_params['read_only_folders'] = \
            ('INBOX.Sent', 1)
        ob = box._addFolder('INBOX', 'INBOX')
        ob2 = ob._addFolder('Sent', 'INBOX.Sent')
        ob2._addMessage('1', '1')
        self.assert_(not ob2.deleteMessage('1'))

        ob3 = ob._addFolder('folder', 'INBOX.folder')
        ob3._addMessage('1', '1')

        self.assert_(not ob3.moveMessage('1', ob2))

    def test_isProtectedProtections(self):
        box = self._getMailBox()
        box._connection_params['protected_folders'] = \
            ('INBOX.Sent', 1)
        box._connection_params['read_only_folders'] = ('', 1)

        ob = box._addFolder('INBOX', 'INBOX')
        ob2 = ob._addFolder('Sent', 'INBOX.Sent')
        ob2._addMessage('1', '1')
        ob3 = ob._addFolder('folder', 'INBOX.folder')
        ob3._addMessage('1', '1')
        self.assert_(not ob3.moveMessage('1', ob2))


    def test_loadMessageStructureFromServer(self):
        # XXX will be move in imap class
        def luid(type_, message_number, message_parts):
            return ('OK', [("""1 (BODY (("text" "plain" ("charset" "iso-8859-1" "format"
         "flowed") NIL NIL "base64" 100 2)(("text" "html" ("charset" "iso-8859-1") NIL
         NIL "7bit" 1207 30)("image" "gif" ("name" "logo_bceao.gif")
          "<part1.01030007.07010309@bceao.lan>" NIL "base64" 4920) "related") "alternative"))""")])

        ob = self.getMailInstance(1)
        box = self._getMailBox()
        realconnector = box._getconnector()._connection
        old = realconnector.uid
        try:
            realconnector.uid = luid
            box._loadMessageStructureFromServer('x', 1, [], {}, 0, ob,
                                                box._getconnector(), True)

            ct = ob._getStore()['Content-type']
            self.assertEquals(ct, 'text/html; charset="iso-8859-1"')
        finally:
            realconnector.uid = old

    def test_loadMessageStructureFromServer2(self):
        # XXX will be move in imap class
        def get_struct(*args, **kw):
            struct = ['report', ['text', 'plain', None, None, 'notification', '8bit', 505, 14], ['message', 'delivery-status', None, None, 'delivery report', '8bit', 369], ['message', 'rfc822', None, None, 'undelivered message', '8bit', 101221, 28, ['fri, 09 sep 2005 06:45:29 -0000', 'test retour', None, None, None, '<71803504.71803504>', [['basicuser', None, 'xxxx1', 'xxxx.com']], [[None, None, 'inexistant.sdflk', 'free.fr']]], ['mixed', ['text', 'plain', None, None, '7bit', 38, 3, ['charset','iso-8859-15']], ['image', 'jpeg', None, None, 'base64', 100352, ['name', 'a broken moment - hommage a la folie pure....1.0.jpg']]]]]

            return struct

        ob = self.getMailInstance(1)
        box = self._getMailBox(True)
        old = box._getconnector().getMessageStructure
        try:
            box._getconnector().getMessageStructure = get_struct

            box._loadMessageStructureFromServer('x', 1, [], {}, 0, ob,
                                                box._getconnector(), True)

            ct = ob._getStore()['Content-type']
            self.assertEquals(ct, 'text/plain; charset="ISO8859-15"')
        finally:
            box._getconnector().getMessageStructure = old

    def test_forceDelete(self):
        # when a folder is placed in the trash
        # it could fail if the max depth is <= 2
        # now forces the folder move in renamefolder
        # if the objective is to send to the trash
        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        folder1 = inbox._addFolder('folder 1', 'INBOX.folder 1')
        trash = inbox._addFolder('Trash', 'INBOX.Trash')
        result = folder1.delete()

        self.assertNotEquals(result, None)

    def test_isSpecialFolder(self):

        mailbox = self._getMailBox()
        inbox = mailbox._addFolder('INBOX', 'INBOX')
        folder1 = inbox._addFolder('folder 1', 'INBOX.folder 1')
        trash = inbox._addFolder('Trash', 'INBOX.Trash')

        self.assert_(not folder1.isSpecialFolder())
        self.assert_(trash.isSpecialFolder())

    def test_loadMessageStructureFromServer3(self):
        # XXX will be move in imap class
        def get_struct(*args, **kw):
            struct = ['mixed', ['related', ['alternative', ['text', 'plain', None, None, 'quoted-printable',
                  162, 18, ['charset', 'iso-8859-1']], ['text', 'html', None, None, 'quoted-printable',
                  4055, 130, ['charset', 'iso-8859-1']]], ['image', 'jpeg', '<image001.jpg@01c5da3d.8e2d4980>',
                  None, 'base64', 2796, ['name', 'image001.jpg']]], ['application', 'msword',
                  None, None, 'base64', 110002, ['name', 'document.doc']]]

            return struct

        ob = self.getMailInstance(1)
        box = self._getMailBox(True)
        old = box._getconnector().getMessageStructure
        try:
            box._getconnector().getMessageStructure = get_struct
            box._loadMessageStructureFromServer('x', 1, [], {}, 0, ob,
                                                box._getconnector(), True)

            ct = ob._getStore()['Content-type']
            self.assertEquals(ct, 'text/html; charset="iso-8859-1"')
            files = ob.getFileList()
            self.assertEquals(files[0]['part'], 2)
            self.assertEquals(files[1]['part'], '1.2')
        finally:
            box._getconnector().getMessageStructure = old

    def test_Interface(self):
        # make sure the contract is respected
        from zope.interface.verify import verifyClass
        self.failUnless(verifyClass(IMailFolder, MailFolder))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailFolderTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailfolder'),
        ))
