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
from Testing.ZopeTestCase import installProduct



class MailSearchTestCase(MailTestCase):

    count = 0
    def fakeGetPhysicalPath(self):
        self.count +=1
        return ('', 'nowere/my_message_' + str(self.count))

    def _getCatalog(self):
        cat = MailCatalog('cat', 'joe')
        cat = cat.__of__(self.portal)
        return cat

    def test_instance(self):
        cat = self._getCatalog()
        self.assertNotEquals(cat, None)
        dict = MailCatalogDict()
        self.assertNotEquals(dict, None)

    def test_indexPresence(self):
        cat = self._getCatalog()
        indexes = cat.getIndexObjects()
        index = indexes[0]
        self.assert_(index.meta_type == 'TextIndexNG')

    def test_indexing(self):
        cat = self._getCatalog()
        ob = self.getMailInstance(15)
        ob = ob.__of__(self.portal)

        cat.indexMessage(ob)

        # verify catalog content
        query ={}
        query['searchable_text'] = u'failed'
        brains = cat.search(query_request=query)
        self.assertEquals(len(brains), 1)
        brain = brains[0]
        rid = brain.getRID()
        datas = cat.getIndexDataForRID(rid)
        self.assertEquals(datas['searchable_text'],
            [u'delivery', u'notification', u'has', u'failed',
             u'scr', u'admin', u'socal', u'raves', u'org',
             u'internet', u'mail', u'postmaster', u'ucla', u'edu'])

    def test_search(self):
        cat = self._getCatalog()

        ob = self.getMailInstance(15)

        cat.indexMessage(ob)
        # verify if it's done
        query ={}
        query['searchable_text'] = u'dzoduihgzi'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 0)

        query['searchable_text'] = u'delivery'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 1)

    def test_search_cat(self):

        cat = self._getCatalog()

        for i in range(35):
            ob = self.getMailInstance(i)
            ob = ob.__of__(self.portal)
            ob.getPhysicalPath = self.fakeGetPhysicalPath
            cat.indexMessage(ob)

        query = {}
        query['searchable_text'] = u'something'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 2)

        query = {}
        query['searchable_text'] = u'Dingus Lovers'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 7)

    def test_wrapMessage(self):
        # at this time, wrapping a message is just for
        # subject, to and from sections
        cat = self._getCatalog()
        msg = self.getMailInstance(15)
        cat.wrapMessage(msg)
        wrap = msg.searchable_text
        wrap_list = wrap.split(' ')

        # subject
        subject = msg.getHeader('Subject')[0]
        words = subject.split(' ')
        for word in words:
            self.assert_(word in wrap_list)

        # from
        froms = msg.getHeader('From')
        for word in froms:
            if word.find('@')==-1:
                self.assert_(word in wrap_list)

        # tos
        tos = msg.getHeader('To')
        for word in tos:
            if word.find('@')==-1:
                self.assert_(word in wrap_list)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailSearchTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailsearch'),
        ))
