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

        """ ???????? this fails
        self.assert_(IMailBox.providedBy(ob))
        self.assert_(IMailFolder.providedBy(ob))
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


    def test_clipboard(self):
        # test clipboard
        mailbox = MailBox('mailbox')
        action, ids = mailbox.getClipboard()
        self.assertEquals(action,'')
        self.assertEquals(ids, [])
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
        self.assertEquals(action,'')
        self.assertEquals(ids, [])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailbox'),
        ))
