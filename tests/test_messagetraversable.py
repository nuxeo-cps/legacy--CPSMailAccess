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

import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
from Products.CPSMailAccess.interfaces import IMessageTraverser, IMailMessage
from Products.CPSMailAccess.messagetraversable import MessageTraversable
from Products.CPSMailAccess.mailmessage import MailMessage

installProduct('FiveTest')
installProduct('Five')

class FakeRequest:

    maybe_webdav_client = False

    def getPresentationSkin(self):
        return None

    def get(self, element1, element2):
        return ''


class MessageTraversableTestCase(ZopeTestCase):

    def test_SimpleInstance(self):
        # mailmessageedit view
        ob = MailMessage('ok')
        mt = MessageTraversable(ob)
        self.assert_(mt)
        return mt

    def test_traverse(self):

        req = FakeRequest()
        ob = MailMessage('ok')
        ob.REQUEST = req

        # testing hasattr
        ob2 = MailMessage('sub_message')
        mt = MessageTraversable(ob)
        result = mt.traverse('sub_message', req)
        self.assertEquals(result.getId(), 'sub_message')

        # testing on the fly creation
        mt = MessageTraversable(ob)
        result = mt.traverse('sub_message_part2', req)
        self.assertEquals(result.getId(), 'sub_message_part2')

        # testing that it is made available in _v_volatile_parts
        self.assert_(ob._v_volatile_parts.has_key('sub_message_part2'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MessageTraversableTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.messagetraversable'),
        ))
