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
import os, sys
from CPSMailAccess.mailsearch \
    import MailCatalog, MailCatalogDict


from basetestcase import MailTestCase

class MailSearchTestCase(MailTestCase):

    def test_instance(self):
        cat = MailCatalog('cat', 'joe')
        self.assertNotEquals(cat, None)

        dict = MailCatalogDict()
        self.assertNotEquals(dict, None)

    def test_indexing(self):
        cat = MailCatalog('cat', 'joe')
        ob = self.getMailInstance(7)

        cat.indexMessage(ob)
        # verify if it's done
        res = cat.search('*')
        self.assertEquals(len(res), 1)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailSearchTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailsearch'),
        ))
