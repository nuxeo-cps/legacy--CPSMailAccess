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
from Products.CPSMailAccess.mailbox import MailBox, MailBoxParametersView, \
    MailMessageEdit
from basetestcase import MailTestCase

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
        ob = MailBox('mailbox')
        self.assertEquals(IMailBox.providedBy(ob), True)

        # WHY THIS IS FAILING ????
        """
        ob = self._getMailBox()

        self.assertEquals(self.portal.INBOX, ob)

        self.assertEquals(IMailFolder.providedBy(ob), True)
        self.assertEquals(IMailBox.providedBy(ob), True)
        """

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

    def test_MailMessageEdit(self):
        # mailmessageedit view
        mailbox = MailBox('mailbox')
        view = MailMessageEdit(mailbox, None)
        self.assertNotEquals(view, None)

    def test_attach_file(self):
        mailbox = self._getMailBox()
        msg = mailbox.getCurrentEditorMessage()
        msg.setPart(0, 'the body')
        self.assert_(not msg.isMultipart())
        my_file = self._openfile('PyBanner048.gif')
        storage = FakeFieldStorage()
        storage.file = my_file
        storage.filename = 'PyBanner048.gif'

        uploaded = FileUpload(storage)
        view = MailMessageEdit(mailbox, None)
        self.assertNotEquals(view, None)
        view.attachFile(uploaded)

        # now verify the result
        self.assert_(msg.isMultipart())
        self.assertEquals(msg.getPartCount(), 2)
        self.assertNotEquals(msg.getPart(1), None)

        # for reuse
        return (msg, view)

    def test_detachFile(self):
        mailbox = self._getMailBox()
        ret = self.test_attach_file()
        msg = ret[0]
        view = ret[1]
        view.detachFile('PyBanner048.gif')
        # now verify the result
        self.assert_(not msg.isMultipart())
        # check that the message is okby re-attaching a file
        ret = self.test_attach_file()

    ### need more tests here on EditorMessage


    def test_getSpecialFolders(self):
        mailbox = self._getMailBox()
        mailbox._addFolder('Trash')
        mailbox._addFolder('Sent')
        mailbox._addFolder('Drafts')

        self.assertEquals(mailbox.getTrashFolderName(), 'INBOX.Trash')
        self.assertEquals(mailbox.getTrashFolder(), mailbox.INBOX.Trash)
        self.assertEquals(mailbox.getSentFolderName(), 'INBOX.Sent')
        self.assertEquals(mailbox.getSentFolder(), mailbox.INBOX.Sent)
        self.assertEquals(mailbox.getDraftFolderName(), 'INBOX.Drafts')
        self.assertEquals(mailbox.getDraftFolder(), mailbox.INBOX.Drafts)

    def test_getCurrentEditorMessage(self):
        mailbox = self._getMailBox()
        msg = mailbox.getCurrentEditorMessage()
        self.assertEquals(msg, mailbox._v_current_editor_message)
        date = msg.getHeader('Date')
        # must be the same msg
        msg = mailbox.getCurrentEditorMessage()
        date2 = msg.getHeader('Date')
        self.assertEquals(date, date2)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailbox'),
        ))
