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

from Products.CPSMailAccess.mailcache import MailCache
from Products.CPSMailAccess.interfaces import IMailMessageCache, IMailMessage
from Products.CPSMailAccess.mailmessage import MailMessage

installProduct('Five')

class MailCacheTestCase(ZopeTestCase):

    def msgKeyGen(self):
        result = 'msg_' + str(self.msg_key)
        self.msg_key += 1
        return result

    def test_set(self):
        cache = MailCache()

        m1 = MailMessage()
        d1 = 'uniqueid'
        cache[d1] = m1
        self.assertEquals(len(cache), 1)

        # Set again
        cache[d1] = m1
        self.assertEquals(len(cache), 1)

        m2 = MailMessage()
        d2 = 'otherid'
        cache[d2] = m2
        self.assertEquals(len(cache), 2)

    def test_clear(self):
        cache = MailCache()

        m1 = MailMessage()
        d1 = 'uniqueid'
        cache[d1] = m1
        self.assertEquals(len(cache), 1)

        self.assert_(cache.has_key(d1))
        self.assert_(not cache.has_key('blarg'))

        cache.clear()
        self.assertEquals(len(cache), 0)
        self.assert_(not cache.has_key(d1))
        self.assert_(not cache.has_key('blarg'))

    def test_get(self):
        cache = MailCache()

        m1= MailMessage()
        d1 = 'uniqueid'
        cache[d1] = m1

        m2 = MailMessage()
        d2 = 'uniqueid2'
        cache[d2] = m2

        self.assertEquals(len(cache), 2)

        result = cache.get(d1, remove=False)
        self.assertNotEquals(result, None)

        result = cache.get(d2, remove=True)
        self.assertNotEquals(result, None)
        self.assertEquals(len(cache), 1)

        result = cache.get('barf')
        self.assertEquals(result, None)

        result = cache.get('barf', default=123)
        self.assertEquals(result, 123)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailCacheTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailcache'),
        ))
