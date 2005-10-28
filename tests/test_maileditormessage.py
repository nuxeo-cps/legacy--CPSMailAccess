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
from Testing.ZopeTestCase import ZopeTestCase
from Products.CPSMailAccess.maileditormessage import MailEditorMessage
#from Products.CPSMailAccess.interfaces import IMailMessage, IMailPart

class MailEditorMessageTestCase(ZopeTestCase):

    def test_instance(self):
        ob = MailEditorMessage()
        self.assertNotEquals(ob, None)

    def test_getCacheNothingYet(self):
        ob = MailEditorMessage()
        self.assertEquals(ob.getCachedValue('yo'), None)

    def test_setGetCache(self):
        ob = MailEditorMessage()
        ob.setCachedValue('yo', 123)
        ob.setCachedValue('yodzz', 1232)
        self.assertEquals(ob.getCachedValue('yodzz'), 1232)
        self.assertEquals(ob.getCachedValue('yo'), 123)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailEditorMessageTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.maileditormessage'),
        ))
