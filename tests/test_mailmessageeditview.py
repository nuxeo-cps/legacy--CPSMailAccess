#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2005 Nuxeo SARL <http://nuxeo.com>
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
from Products.CPSMailAccess.mailmessageeditview import MailMessageEdit
from basetestcase import MailTestCase

class FakeFieldStorage:
    file = None
    filename = ''
    headers = []

class MailMessageEditTestCase(MailTestCase):

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

    def test_addRecipient(self):
        mailbox = self._getMailBox()
        msg = mailbox.getCurrentEditorMessage()
        view = MailMessageEdit(mailbox, None)
        view.addRecipient('tziade@nuxeo.com', 'To')
        Tos = msg.getHeader('To')
        self.assertEquals(Tos, ['tziade@nuxeo.com'])
        view.addRecipient('tz@nuxeo.com', 'To')
        Tos = msg.getHeader('To')
        self.assertEquals(Tos, ['tziade@nuxeo.com', 'tz@nuxeo.com'])
        view.removeRecipient('tziade@nuxeo.com', 'To')
        Tos = msg.getHeader('To')
        self.assertEquals(Tos, ['tz@nuxeo.com'])

    def test_getDestList(self):
        mailbox = self._getMailBox()
        msg = mailbox.getCurrentEditorMessage()
        view = MailMessageEdit(mailbox, None)
        view.addRecipient('tziade@nuxeo.com', 'To')
        view.addRecipient('tz@nuxeo.com', 'Cc')
        self.assertEquals(view.getDestList(), [{'type': 'To', 'value': u'tziade@nuxeo.com'},
            {'type': 'Cc', 'value': u'tz@nuxeo.com'}])

    def test_addMultipleRecipients(self):
        mailbox = self._getMailBox()
        msg = mailbox.getCurrentEditorMessage()
        view = MailMessageEdit(mailbox, None)
        view.addRecipient('tziade@nuxeo.com, tarek@ziade.org;tz@nuxeo.com', 'To')

        self.assertEquals(view.getDestList(),
                          [{'type': 'To', 'value': u'tziade@nuxeo.com'},
                           {'type': 'To', 'value': u'tarek@ziade.org'},
                           {'type': 'To', 'value': u'tz@nuxeo.com'}])

    def test_addingPartsThenSends(self):

        mailbox = self._getMailBox()
        msg = mailbox.getCurrentEditorMessage()
        msg.setPart(0, 'the body')
        self.assert_(not msg.isMultipart())

        my_file = self._openfile('PyBanner048.gif')
        storage = FakeFieldStorage()
        storage.file = my_file
        storage.filename = 'PyBanner048.gif'
        uploaded = FileUpload(storage)

        my_file2 = self._openfile('PyBanner048.gif')
        storage2 = FakeFieldStorage()
        storage2.file = my_file2
        storage2.filename = 'SecondPyBanner048.gif'
        uploaded2 = FileUpload(storage2)

        my_file3 = self._openfile('PyBanner048.gif')
        storage3 = FakeFieldStorage()
        storage3.file = my_file3
        storage3.filename = 'SecondPyBanner048.gif'
        uploaded3 = FileUpload(storage3)

        view = MailMessageEdit(mailbox, None)
        view.attachFile(uploaded)
        view.attachFile(uploaded2)
        view.attachFile(uploaded3)
        view.detachFile('PyBanner048.gif')

        view.sendMessage('from me', 'subject', 'body')








    ### need more tests here on EditorMessage


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageEditTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessageeditview'),
        ))
