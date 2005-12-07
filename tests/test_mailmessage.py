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
from types import StringType, ListType
import unittest, os
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase, _print

from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.interfaces import IMailMessage

from Products.CPSMailAccess.tests import __file__ as landmark
from basetestcase import MailTestCase, openfile

from zope.publisher.browser import FileUpload

# XXXXXXXXX todo : move part tests to test_mailpart.py

class FakeFieldStorage:
    file = None
    filename = ''
    headers = []


class MailMessageTestCase(MailTestCase):

    def getAllMails(self):
        res = []
        for i in range(51):
            ob = MailMessage()
            if i < 9:
                data = self._msgobj('msg_0'+str(i+1)+'.txt')
            else:
                data = self._msgobj('msg_'+str(i+1)+'.txt')

            if data <> '':
                ob.loadMessage(data)
                res.append(ob)
        return res

    def test_base(self):
        # loading a lot of different mails
        ob = MailMessage()
        for i in range(51):
            if i < 9:
                data = self._msgobj('msg_0'+str(i+1)+'.txt')
            else:
                data = self._msgobj('msg_'+str(i+1)+'.txt')

            if data <> '':
                ob.loadMessage(data)

    def test_getCharset(self):
        # testing charsets on msg_07.txt
        ob = self.getMailInstance(7)

        self.assertEquals(ob.getCharset(), None)
        """
        self.assertEquals(ob.getCharset(1), "us-ascii")
        self.assertEquals(ob.getCharset(2), "iso-8859-1")
        self.assertEquals(ob.getCharset(3), "iso-8859-2")
        """

        ob = self.getMailInstance(2)
        self.assertEquals(ob.getCharset(), None)


    def test_getsetCharset(self):
        # testing charsets on msg_07.txt
        ob = self.getMailInstance(7)
        self.assertEquals(ob.getCharset(), None)
        ob.setCharset("iso-8859-1")
        self.assertEquals(ob.getCharset(), "iso-8859-1")

        ob = self.getMailInstance(2)
        self.assertEquals(ob.getCharset(), None)
        ob.setCharset("iso-8859-1")
        self.assertEquals(ob.getCharset(), "iso-8859-1")

    def test_getContentType(self):
        # testing getContentType
        ob = self.getMailInstance(6)

        ct = ob.getContentType()
        self.assertEquals(ct, 'multipart/mixed')

        ob = self.getMailInstance(2)

        ct = ob.getContentType()
        self.assertEquals(ct, 'text/plain')

    def test_setContentType(self):
        # testing setContentType
        ob = self.getMailInstance(6)

        ct = ob.getContentType()
        self.assertEquals(ct, 'multipart/mixed')
        ob.setContentType('text/plain')
        ct = ob.getContentType()
        self.assertEquals(ct, 'text/plain')

    def test_getParams(self):
        # testing getParams
        ob = self.getMailInstance(6)

        ct = ob.getParams()
        self.assertEquals(ct, [('multipart/mixed', ''), ('boundary', 'BOUNDARY')])

        ct = ob.getParam('boundary')
        self.assertEquals(ct, 'BOUNDARY')

        ob = self.getMailInstance(2)

        ct = ob.getParams()
        self.assertEquals(ct, None)

    def test_setParams(self):
        # testing getParams
        ob = self.getMailInstance(6)

        ob.setParam('boundary', 'FRONTIERE')
        ct = ob.getParams()
        self.assertEquals(ct, [('multipart/mixed', ''), ('boundary', 'FRONTIERE')])
        ct = ob.getParam('boundary')
        self.assertEquals(ct, 'FRONTIERE')

        ob = self.getMailInstance(2)
        ob.setParam('boundary', 'FRONTIERE')
        ct = ob.getParam('boundary')
        self.assertEquals(ct, 'FRONTIERE')

    def test_delParams(self):
        # testing getParams
        ob = self.getMailInstance(6)

        ob.setParam('boundary', 'FRONTIERE')
        ob.delParam('boundary')
        ct = ob.getParam('boundary')
        self.assertEquals(ct, None)

        ob = self.getMailInstance(2)
        ob.setParam('boundary', 'FRONTIERE')
        ob.delParam('boundary')
        ct = ob.getParam('boundary')
        self.assertEquals(ct, None)

    def test_getHeaders(self):
        ob = self.getMailInstance(6)

        self.assertEquals(ob.getHeader('From'), ['Barry <barry@digicool.com>'])
        # must be case insensitive
        self.assertEquals(ob.getHeader('from'), ['Barry <barry@digicool.com>'])

    def test_setHeaders(self):
        ob = MailMessage()
        s = 'Tarek <tz@nuxeo.com>'
        ob.setHeader('From', s)
        self.assertEquals(ob.getHeader('From'), [s])
        self.assertEquals(ob.getHeader('from'), [s])

        s = 'Tarek <tarek@ziade.org>'
        ob.setHeader('From', s)
        self.assertEquals(ob.getHeader('From'), [s])
        self.assertEquals(ob.getHeader('from'), [s])

        s = 'Bob <bob@dinosaur.org>'
        ob.setHeader('from', s)
        self.assertEquals(ob.getHeader('From'), [s])
        self.assertEquals(ob.getHeader('from'), [s])

    def test_copyFrom(self):
        ob = self.getMailInstance(6)
        ob2 = MailMessage('uid2', 'uid2')
        ob2.copyFrom(ob)
        self.assertNotEquals(ob.uid, ob2.uid)
        self.assertEquals(ob.seen, ob2.seen)

    def test_copyFromHeaders(self):
        ob = self.getMailInstance(6)
        ob2 = MailMessage('uid2', 'uid2')
        ob2.copyFrom(ob)
        self.assertEquals(ob2.getHeader('Subject') , ob.getHeader('Subject'))

    def test_copyFromVerifyValues(self):
        ob = self.getMailInstance(6)
        ob.junk = 1
        ob.size = 13
        ob2 = MailMessage('uid2', 'uid2')
        ob2.copyFrom(ob)
        self.assertNotEquals(ob.uid, ob2.uid)
        self.assertEquals(ob.seen, ob2.seen)
        self.assertEquals(ob2.junk, 1)
        self.assertEquals(ob2.size, 13)

    def test_attachPart(self):
        ob = self.getMailInstance(2)
        initial_message = ob.getRawMessage()

        file = openfile('audiotest.au')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'audiotest.au'
        uploaded = FileUpload(storage)
        ob.attachFile(uploaded)
        message_and_attachment = ob.getRawMessage()

        # just checking that the file was included
        pos = message_and_attachment.find('bq2waywxcnn/zZBSUVJ07zFwbjN501NND')
        self.assertNotEquals(pos, -1)

    def test_attachfile(self):
        ob = self.getMailInstance(2)
        initial_message = ob.getRawMessage()

        file = openfile('audiotest.au')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'audiotest.au'
        uploaded = FileUpload(storage)

        ob.attachFile(uploaded)

        files = ob.getFileList()
        self.assertEquals(files[0]['mimetype'], 'audio/basic')
        self.assertEquals(files[0]['filename'], 'audiotest.au')

        file = openfile('PyBanner048.gif')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'PyBanner048.gif'
        uploaded = FileUpload(storage)
        ob.attachFile(uploaded)

        files = ob.getFileList()
        self.assertEquals(files[1]['filename'], 'PyBanner048.gif')

        message_and_attachment = ob.getRawMessage()

        # just checking that the files were included
        pos = message_and_attachment.find('PyBanner048.gif')
        self.assertNotEquals(pos, -1)
        pos = message_and_attachment.find('audiotest.au')
        self.assertNotEquals(pos, -1)

        ob.detachFile('PyBanner048.gif')
        ob.detachFile('audiotest.au')

        files = ob.getFileList()
        self.assertEquals(len(files), 0)

    def test_hasAttachment(self):
        ob = self.getMailInstance(2)
        self.assert_(not ob.hasAttachment())

        file = openfile('audiotest.au')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'audiotest.au'
        uploaded = FileUpload(storage)
        ob.attachFile(uploaded)

        self.assert_(ob.hasAttachment())

    def test_flags(self):
        # testing get an set flags and triggering
        ob = self.getMailInstance(35)

        self.assertEquals(ob.getFlag('seen'), 0)
        ob.setFlag('seen', 1)
        self.assert_(ob.getFlag('seen') == 1)

    def test_getDirectBody(self):
        ob = self.getMailInstance(35)
        body = ob.getDirectBody()
        self.assertNotEquals(body, '')
        ob.setDirectBody('okay')
        self.assertEquals(ob.getDirectBody(), 'okay')

    def test_messageIdGen(self):
        ob = self.getMailInstance(35)
        ob.setHeader('Message-ID', '')
        self.assertEquals(ob.getHeader('Message-ID'), [''])
        msg = ob.getRawMessage()
        self.assertNotEquals(ob.getHeader('Message-ID')[0], '<>')
        self.assertNotEquals(ob.getHeader('Message-ID')[0], '<%d.%d>' % (id(ob), id(ob)))
        ob.uid = '876576'
        msg = ob.getRawMessage()
        self.assertNotEquals(ob.getHeader('Message-ID')[0], '<876576>')

    def test_hasAttachment2(self):
        ob = MailMessage()
        self.assert_(not ob.hasAttachment())

    def dtest_attachMessage(self):
        # attaching message was busting the mail
        # XXXX need to change this test
        # so it works exactly like the real case
        ob = self.getMailInstance(35)
        file = openfile('msg_35.txt')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'msg_35.txt'
        uploaded = FileUpload(storage)

        ob.attachFile(uploaded)

        # check that an attached message does not bust the message
        ob.getRawMessage()

    def test_loadMessage(self):
        # chechking for multiple headers
        ob = self.getMailInstance(43)
        headers = [('cc', 'toto'), ('cc', 'toti')]
        ob.loadMessage(headers=headers)
        self.assertEquals(ob.getHeader('cc'), ['toto', 'toti'])

    def test_BCcLoose(self):
        # we have to be able to keep BCc headers
        ob = self.getMailInstance(43)
        headers = [('bcc', 'toto'), ('bcc', 'toti')]
        ob.loadMessage(headers=headers)
        raw_msg = ob.getRawMessage()
        self.assertNotEquals(raw_msg.find('toto'), -1)
        self.assertNotEquals(raw_msg.find('toti'), -1)

    def test_Interface(self):
        # make sure the contract is respected
        from Interface.Verify import verifyClass
        self.failUnless(verifyClass(IMailMessage, MailMessage))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessage'),
        ))
