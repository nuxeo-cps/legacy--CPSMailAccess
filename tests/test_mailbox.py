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

import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase

from Products.CPSMailAccess.mailbox import MailBox
from Products.CPSMailAccess.interfaces import IMailBox


installProduct('FiveTest')
installProduct('Five')


class MailBoxTestCase(ZopeTestCase):

    msg_key = 0

    def msgKeyGen(self):
        result = 'msg_' + str(self.msg_key)
        self.msg_key += 1
        return result

    def test_base(self):
        """ single instance
        """
        ob = MailBox()
        self.assertNotEquals(ob, None)

    def test_synchronize(self):
        """ testing synchronize calls
        """
        mailbox = MailBox()

        for i in range(10):
            ob = mailbox._addFolder()

            for i in range(10):
                ob._addFolder()

            for i in range(123):
                key = self.msgKeyGen()
                ob._addMessage(key, key)

        mailbox.synchronize()

    def test_paramMapping(self):
        """ testing mapping
        """
        mailbox = MailBox()

        mailbox['uid'] = 'tarek'
        mailbox['connection_type'] = 'IMAP'
        self.assertEquals('IMAP', mailbox['connection_type'])
        self.assertEquals('tarek', mailbox['uid'])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailbox'),
        ))
