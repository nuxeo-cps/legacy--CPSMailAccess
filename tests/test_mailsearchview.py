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
from Products.CPSMailAccess.mailsearchview import MailSearchView
from Products.CPSMailAccess.mailbox import MailBox

from basetestcase import MailTestCase

class MailSearchViewTestCase(MailTestCase):

    def _getView(self):
        """ for test purpose,
            we create one catalog for the user "bob"
            with a few mails indexed
        """
        wm = self.portal.portal_webmail
        wm.mail_catalogs.addCatalog('bob')

        cat = wm.mail_catalogs['bob']

        for i in range(35):
            ob = self.getMailInstance(i)
            ob = ob.__of__(self.portal)
            cat.indexMessage(ob)

        box = self._getMailBox()
        searchview = MailSearchView(box, self.request)
        searchview = searchview.__of__(box)
        return searchview

    def test_instanciation(self):
        searchview = self._getView()
        self.assertNotEquals(searchview, None)

    def test_getting_the_right_catalog(self):
        searchview = self._getView()
        cat = searchview._getCatalog('bob')
        self.assertNotEquals(cat, None)
        self.assertEquals(cat.user_id, 'bob')

    def test_searchs(self):
        searchview = self._getView()

        results = searchview.search('bob', 'like')
        self.assertEquals(results, '')



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailSearchViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailsearchview'),
        ))
