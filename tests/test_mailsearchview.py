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

    count = 0
    def fakeGetPhysicalPath(self):
        self.count +=1
        return ('', 'nowere/my_message_' + str(self.count))

    def _getView(self):
        """ for test purpose,
            we create one catalog for the user "bob"
            with a few mails indexed
        """
        box = self._getMailBox()
        cat = box._getCatalog()

        for i in range(35):
            ob = self.getMailInstance(i)
            ob.getPhysicalPath = self.fakeGetPhysicalPath
            ob = ob.__of__(self.portal)
            cat.indexMessage(ob)

        searchview = MailSearchView(box, self.request)
        searchview = searchview.__of__(box)
        return searchview, cat, box

    def test_instanciation(self):
        searchview = self._getView()
        self.assertNotEquals(searchview, None)

    def test_searchs(self):
        searchview, cat, box = self._getView()    # also fills cat
        self.assertEquals(box._getCatalog(), cat)
        query = {}
        query['searchable_text'] = u'Lovers'

        res = cat.search(query_request=query)
        direct_search = []
        for brain in res:
            direct_search.append(brain.getPath())

        results = searchview.searchMessages('Dingus Lovers')

        for res in results:
            self.assert_(res['path'] in direct_search)

    def test_weirdo_searchs(self):

        searchview, cat, box = self._getView()    # also fills cat
        results = searchview.searchMessages('é')





def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailSearchViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailsearchview'),
        ))
