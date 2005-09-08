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

    def _getView(self, full_indexation=True):
        """ for test purpose,
            we create one catalog for the user "bob"
            with a few mails indexed
        """
        box = self._getMailBox()
        zcat = box._getZemanticCatalog()

        for i in range(38):
            ob = self.getMailInstanceT(i)
            ob.getPhysicalPath = self.fakeGetPhysicalPath
            ob = ob.__of__(self.portal)
            zcat.indexMessage(ob, full_indexation)

        searchview = MailSearchView(box, self.request)
        searchview = searchview.__of__(box)
        return searchview, None, zcat, box

    def test_instanciation(self):
        searchview = self._getView()
        self.assertNotEquals(searchview, None)

    def test_zemanticPredicateList(self):
        searchview, cat, zcat, box = self._getView()    # also fills cat
        list_ = searchview.zemanticPredicateList()
        self.assertEquals(list_, [u'body', u'cc', u'content-description',
                                  u'content-disposition',
                                  u'content-transfer-encoding',
                                  u'content-type', u'date', u'delivered-to',
                                  u'errors-to', u'from', u'list-archive',
                                  u'list-help', u'list-id', u'list-post',
                                  u'list-subscribe', u'list-unsubscribe',
                                  u'message-id', u'mime-version',
                                  u'precedence', u'received', u'reply-to',
                                  u'return-path', u'sender', u'status',
                                  u'subject', u'to', u'user-agent', u'x-aid',
                                  u'x-attribution', u'x-beenthere', u'x-caid',
                                  u'x-copyrighted-material', u'x-cuid',
                                  u'x-foobar-spoink-defrobnit', u'x-loop',
                                  u'x-mailer', u'x-mailman-version',
                                  u'x-mimetrack', u'x-oblique-strategy',
                                  u'x-organization', u'x-priority',
                                  u'x-spam-status', u'x-trid', u'x-uidl',
                                  u'x-url'])

    def test_zemantic_searchs(self):
        searchview, cat, zcat, box = self._getView()    # also fills cat


        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = '*'    # all
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]

        # results order won't be known
        self.assertEquals(len(results), 3)

        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = 'ccc*'
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]

        self.assertEquals(len(results), 1)

        # trying intersections
        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = 'ccc*'
        query['intersection'] = 'store is open'
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]

        self.assertEquals(len(results), 1)

        # trying intersections
        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = '*'
        query['relation_1'] = 'subject'        # relations keys are normalized (lower)
        query['value_1'] = 'test'
        query['intersection'] = 'store is open'
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]

        self.assertEquals(len(results), 1)

        query = {}
        query['intersection'] = 'store is open'
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]
        self.assertEquals(len(results), 0)

    def test_instanciation_light(self):
        searchview = self._getView(False)
        self.assertNotEquals(searchview, None)

    def test_zemanticPredicateList_light(self):
        searchview, cat, zcat, box = self._getView(False)
        list_ = searchview.zemanticPredicateList()
        self.assertEquals(list_, [u'cc', u'date', u'from', u'message-id',
                                  u'sender', u'subject', u'to'])

    def test_zemantic_searchs_light(self):
        searchview, cat, zcat, box = self._getView(False)

        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = '*'    # all
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]

        # results order won't be known
        self.assertEquals(len(results), 3)

        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = 'ccc*'
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]

        self.assertEquals(len(results), 1)

        # trying intersections
        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = 'ccc*'
        query['intersection'] = 1
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]

        self.assertEquals(len(results), 1)

        # trying intersections
        query = {}
        query['relation_0'] = 'cc'        # relations keys are normalized (lower)
        query['value_0'] = '*'
        query['relation_1'] = 'subject'        # relations keys are normalized (lower)
        query['value_1'] = 'test'
        query['intersection'] = 1
        query['lazy_search'] = 1

        results = searchview.zemanticSearchMessages(**query)[0]

        self.assertEquals(len(results), 1)

        query = {}
        query['intersection'] = 1
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]
        self.assertEquals(len(results), 0)

    def test_HeaderSearch(self):
        searchview, cat, zcat, box = self._getView(False)

        query = {}
        query['relation_0'] = 'from'        # relations keys are normalized (lower)
        query['value_0'] = u'Father'
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]
        self.assertEquals(len(results), 1)

        query = {}
        query['relation_0'] = 'from'        # relations keys are normalized (lower)
        query['value_0'] = u'"Father Time"'
        query['lazy_search'] = 1
        results = searchview.zemanticSearchMessages(**query)[0]
        self.assertEquals(len(results), 1)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailSearchViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailsearchview'),
        ))
