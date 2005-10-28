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
from Products.CPSMailAccess.mailboxtreeview import MailBoxTreeView, \
    manage_addMailBoxTreeview
from Products.CPSMailAccess.interfaces import IMailBox

installProduct('Five')

class MailBoxViewTestCase(ZopeTestCase):

    def _setObject(self, id, ob):
        setattr(self, id, ob)

    def test_base(self):
        # simple instanciation
        ob = MailBoxTreeView('mailboxtreeview')
        self.assertNotEquals(ob, None)

    def test_adder(self):
        # dispatcher adder
        dispatcher = self
        manage_addMailBoxTreeview(dispatcher, 'mailboxtreeview')
        self.assert_(hasattr(dispatcher, 'mailboxtreeview'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailboxtreeview'),
        ))
