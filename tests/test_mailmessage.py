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
from types import StringType, ListType
import unittest, os
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase, _print

from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.interfaces import IMailMessage

from CPSMailAccess.tests import __file__ as landmark
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
        for i in range(35):
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
        ob.cache_level = 2
        for i in range(35):
            if i < 9:
                data = self._msgobj('msg_0'+str(i+1)+'.txt')
            else:
                data = self._msgobj('msg_'+str(i+1)+'.txt')

            if data <> '':
                ob.loadMessage(data)


    def test_getPartCount(self):
        # testing part count on msg_07.txt
        ob = self.getMailInstance(7)
        part_count = ob.getPartCount()
        self.assertEquals(part_count, 4)

        ob = self.getMailInstance(2)
        part_count = ob.getPartCount()
        self.assertEquals(part_count, 1)


    def test_getCharset(self):
        # testing charsets on msg_07.txt
        ob = self.getMailInstance(7)

        self.assertEquals(ob.getCharset(0), None)
        self.assertEquals(ob.getCharset(1), "us-ascii")
        self.assertEquals(ob.getCharset(2), "iso-8859-1")
        self.assertEquals(ob.getCharset(3), "iso-8859-2")

        ob = self.getMailInstance(2)
        self.assertEquals(ob.getCharset(), None)


    def test_getCharset(self):
        # testing charsets on msg_07.txt
        ob = self.getMailInstance(7)
        self.assertEquals(ob.getCharset(1), "us-ascii")
        ob.setCharset("iso-8859-1", 1)
        self.assertEquals(ob.getCharset(1), "iso-8859-1")

        ob = self.getMailInstance(2)
        self.assertEquals(ob.getCharset(), None)
        ob.setCharset("iso-8859-1")
        self.assertEquals(ob.getCharset(), "iso-8859-1")

    def test_isMultipart(self):
        # testing Multipart
        ob = self.getMailInstance(7)
        self.assertEquals(ob.isMultipart(), True)

        ob = self.getMailInstance(2)
        self.assertEquals(ob.isMultipart(), False)

    def test_getContentType(self):
        # testing getContentType
        ob = self.getMailInstance(6)

        ct = ob.getContentType()
        self.assertEquals(ct, 'multipart/mixed')

        ct = ob.getContentType(1)
        self.assertEquals(ct, 'text/plain')

        ct = ob.getContentType(2)
        self.assertEquals(ct, 'image/gif')

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

        ct = ob.getContentType(1)
        self.assertEquals(ct, 'text/plain')
        ob.setContentType('image/gif', 1)
        ct = ob.getContentType(1)
        self.assertEquals(ct, 'image/gif')

    def test_getParams(self):
        # testing getParams
        ob = self.getMailInstance(6)

        ct = ob.getParams()
        self.assertEquals(ct, [('multipart/mixed', ''), ('boundary', 'BOUNDARY')])

        ct = ob.getParam('boundary')
        self.assertEquals(ct, 'BOUNDARY')

        ct = ob.getParams(1)
        self.assertEquals(ct, [('text/plain', ''), ('charset', 'us-ascii')])

        ct = ob.getParams(2)
        self.assertEquals(ct, [('image/gif', ''), ('name', 'dingusfish.gif')])

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

        ob.setParam('boundary', 'FRONTIERE', 1)
        ct = ob.getParams(1)
        self.assertEquals(ct, [('text/plain', ''), ('charset', 'us-ascii'),
            ('boundary', 'FRONTIERE')])
        ct = ob.getParam('boundary', 1)
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

        ob.setParam('boundary', 'FRONTIERE', 1)
        ob.delParam('boundary', 1)
        ct = ob.getParam('boundary', 1)
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
        ob.cache_level = 2

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

    def test_partialMessages(self):
        ob = self.getMailInstance(6)
        count = ob.getPartCount()
        self.assertEquals(count, 2)

        self.assertEquals(ob.getPersistentPartIds(), [0, 1])

        # supress a part
        ob.setPart(1, None)
        self.assertEquals(ob.getPart(1), None)

        # testing if it's the persistent list
        self.assertEquals(ob.getPersistentPartIds(), [0])

        # try to reload it as a volatile part
        vp = ob.loadPart(1, 'dfghj', volatile=True)

        self.assertEquals(ob.getPart(1), None)
        self.assertEquals(vp, ob.getVolatilePart(1))
        self.assertNotEquals(ob.getVolatilePart(1), 'dfghj')
        self.assertEquals(ob.getVolatilePart(1).as_string(), '\ndfghj\n')

    def test_copyFrom(self):
        ob = self.getMailInstance(6)
        ob2 = MailMessage('uid2', 'uid2')
        ob2.copyFrom(ob)
        self.assertNotEquals(ob.uid, ob2.uid)
        self.assertEquals(ob.volatile_parts, ob2.volatile_parts)
        self.assertEquals(ob.read, ob2.read)

    def test_copyFromHeaders(self):
        ob = self.getMailInstance(6)
        ob2 = MailMessage('uid2', 'uid2')
        ob2.copyFrom(ob)
        self.assertEquals(ob2.getHeader('Subject') , ob.getHeader('Subject'))


    def test_attachfile(self):
        ob = self.getMailInstance(2)
        initial_message = ob.getRawMessage()

        file = openfile('audiotest.au')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'audiotest.au'
        uploaded = FileUpload(storage)

        ob.attachFile(uploaded)
        raw = ob.getRawMessage()

        self.assertNotEquals(raw.find('AAAAAAABnZ+fn59PNzefnZ1tbZ1'), -1)

        file = openfile('PyBanner048.gif')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'PyBanner048.gif'
        uploaded = FileUpload(storage)
        ob.attachFile(uploaded)

        raw = ob.getRawMessage()
        self.assertNotEquals(raw.find('PyBanner'), -1)

        ob.detachFile('PyBanner048.gif')
        ob.detachFile('audiotest.au')
        # to be thaught
        #self.assertEquals(ob.getRawMessage(), initial_message)

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

    def test_multipartAlternativeRead(self):
        ob = self.getMailInstance(35)
        # lotus note mail message
        # let's try to read the body
        mailpart = ob.getPart(0)
        subpart_1 = mailpart._payload[0]
        self.assert_(subpart_1._payload.startswith('sqdsqd'))



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessage'),
        ))
