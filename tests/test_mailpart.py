#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
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
import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
import os
from Products.CPSMailAccess.mailpart import MailPart
from Products.CPSMailAccess.mailmessage import MailMessage

from basetestcase import MailTestCase

class MailPartTestCase(MailTestCase):

    def test_instance(self):
        part = MailPart('id', None, None)
        self.assert_(part)

    def test_getParent(self):
        msg = MailMessage('id', 'sid')
        part = MailPart('id', msg, None)
        self.assertEquals(part.getParent(), msg)

    def test_getFileInfos(self):
        # testing getParams
        ob = self.getMailInstance(6)
        part = MailPart('part', ob, ob.getPart(1))
        infos = part.getFileInfos()
        self.assertEquals(infos['filename'], 'dingusfish.gif')
        self.assertEquals(infos['mimetype'], 'image/gif')
        part = MailPart('part', ob, ob.getPart(0))
        self.assertEquals(part.getFileInfos(), None)

    def test_setgetaddHeaders(self):
        ob = self.getMailInstance(6)
        ob.setHeader('Subject', 'one')
        ob.setHeader('Subject', 'one')
        headers = ob.getHeader('Subject')
        self.assertEquals(headers, ['one'])

        ob.addHeader('To', 'one')
        ob.addHeader('To', 'two')
        ob.addHeader('To', 'three')
        headers = ob.getHeader('To')
        self.assertEquals(headers, ['Dingus Lovers <cravindogs@cravindogs.com>',
                                    'one', 'two', 'three'])

        ob.removeHeader('To')
        headers = ob.getHeader('To')
        self.assertEquals(headers, [])

        ob.addHeader('To', 'one')
        ob.addHeader('To', 'two')
        ob.addHeader('To', 'three')
        ob.removeHeader('To', ['one'])
        headers = ob.getHeader('To')
        self.assertEquals(headers, ['two', 'three'])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailPartTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailpart'),
        ))
