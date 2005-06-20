#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
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
from Products.CPSMailAccess.mailtool import MailTool
from Products.CPSMailAccess.interfaces import IMailTool

installProduct('Five')

class MailToolTestCase(ZopeTestCase):
    def test_base(self):
        # single instance
        ob = MailTool()
        self.assertNotEquals(ob, None)
        self.assertEquals(ob.getId(), 'portal_webmail')

    def test_listConnectionTypes(self):
        # testing list connection types
        ob = MailTool()
        ct = ob.listConnectionTypes()
        self.assertNotEquals(ct , [])

    def test_boxcreation(self):
        ob = MailTool()
        ob.addMailBox('tarek')
        ob.addMailBox('bill')
        self.assert_(hasattr(ob, 'box_tarek'))
        self.assert_(hasattr(ob, 'box_bill'))
        ob.deleteMailBox('bill')
        self.assert_(not hasattr(ob, 'box_bill'))

    def test_getConnection(self):
        ob = MailTool()
        connection_params = {'uid' : 'admin', 'connection_type' : 'DUMMY'}

        # regular connector
        one = ob.getConnection(connection_params)

        # second connector
        two = ob.getConnection(connection_params, 1)

        one_test = ob.getConnection(connection_params)
        two_test = ob.getConnection(connection_params, 1)

        self.assertNotEquals(id(one), id(two))
        self.assertEquals(id(one), id(one_test))
        self.assertEquals(id(two), id(two_test))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailToolTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailtool'),
        ))
