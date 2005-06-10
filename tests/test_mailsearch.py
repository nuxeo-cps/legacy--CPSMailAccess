#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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
from Products.CPSMailAccess.mailsearch \
    import MailCatalog, ZemanticMailCatalog, ZemanticMessageAdapter

from Testing.ZopeTestCase import installProduct
from basetestcase import MailTestCase
from Testing.ZopeTestCase import installProduct
from mailmessage import MailMessage

from zemantic.public import *
from zemantic.query import Query
from rdflib.URIRef import URIRef
from rdflib.Literal import Literal

installProduct('TextIndexNG2')

class MailSearchTestCase(MailTestCase):

    count = 0
    def fakeGetPhysicalPath(self):
        self.count += 1
        return ('', 'nowere/my_message_' + str(self.count))

    def sameGetPhysicalPath(self):
        return ('', 'nowere/i_am_not_moving')

    def _getCatalog(self):
        cat = MailCatalog('cat', 'joe')
        cat = cat.__of__(self.portal)
        return cat

    def test_instance(self):
        cat = self._getCatalog()
        self.assertNotEquals(cat, None)

    def test_indexPresence(self):
        cat = self._getCatalog()
        indexes = cat.getIndexObjects()
        index = indexes[0]
        self.assert_(index.meta_type == 'TextIndexNG2')

    def test_indexing(self):
        cat = self._getCatalog()
        ob = self.getMailInstance(15)
        ob = ob.__of__(self.portal)

        cat.indexMessage(ob)

        # verify catalog content
        query ={}
        query['searchable_text'] = u'notification'
        brains = cat.search(query_request=query)

        self.assertEquals(len(brains), 1)

        brain = brains[0]
        rid = brain.getRID()
        datas = cat.getIndexDataForRID(rid)
        self.assertEquals(datas['searchable_text'],
                          [(u'delivery', 1), (u'notification', 1), (u'has', 1),
                           (u'failed', 1), (u'scr', 3), (u'admin', 1),
                           (u'socal', 3), (u'raves', 3), (u'internet', 1),
                           (u'mail', 1), (u'postmaster', 1), (u'ucla', 2),
                           (u'edu', 4), (u'this', 1), (u'report', 1),
                           (u'relates', 1), (u'to', 3), (u'message', 3),
                           (u'you', 1), (u'sent', 1), (u'with', 1),
                           (u'the', 2), (u'following', 2), (u'header', 1),
                           (u'fields', 1), (u'id', 1), (u'002001c144a6', 1),
                           (u'8752e060', 1), (u'56104586', 1), (u'oxy', 2),
                           (u'date', 1), (u'sun', 1), (u'23', 1), (u'sep', 1),
                           (u'2001', 1), (u'20:10:55', 1), (u'0700', 1),
                           (u'from', 1), (u'ian', 1), (u'henry', 1),
                           (u'henryi', 1), (u'subject', 1), (u'yeah', 1),
                           (u'for', 1), (u'ians', 1), (u'your', 1),
                           (u'cannot', 1), (u'be', 1), (u'delivered', 1),
                           (u'recipients', 1), (u'recipient', 2), (u'address', 1),
                           (u'jangel1', 1), (u'cougar', 1), (u'noc', 1),
                           (u'reason', 1), (u'reached', 1), (u'disk', 1),
                           (u'quota', 1)])

    def test_unindexing(self):
        cat = self._getCatalog()
        ob = self.getMailInstance(15)
        ob = ob.__of__(self.portal)
        ob.getPhysicalPath = self.sameGetPhysicalPath

        cat.indexMessage(ob)

        # verify catalog content
        query ={}
        query['searchable_text'] = u'notification'
        brains = cat.search(query_request=query)
        self.assertEquals(len(brains), 1)

        cat.unIndexMessage(ob)
        brains = cat.search(query_request=query)
        self.assertEquals(len(brains), 0)


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

    def test_brain_render(self):
        cat = self._getCatalog()
        cat = cat.__of__(self.portal)
        ob = self.getMailInstance(15)
        ob = ob.__of__(self.portal)

        cat.indexMessage(ob)

        # verify if it's done
        query = {}
        query['searchable_text'] = u'delivery'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 1)
        brain = res[0]
        path = brain.getPath()
        self.assertEquals(ob.absolute_url(), path)

    def test_search_cat(self):

        cat = self._getCatalog()

        for i in range(37):
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

    def test_body_search_cat(self):

        cat = self._getCatalog()

        for i in range(37):
            ob = self.getMailInstance(i)
            ob = ob.__of__(self.portal)
            ob.getPhysicalPath = self.fakeGetPhysicalPath
            cat.indexMessage(ob)

        query = {}
        query['searchable_text'] = u'like'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 4)

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

    def test_wrapBuggyMessage(self):
        cat = self._getCatalog()
        msg = self.getMailInstance(15)

        # empty body
        msg.setDirectBody('')

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

    def test_accentsSearches(self):
        cat = self._getCatalog()

        for i in range(37):
            ob = self.getMailInstance(i)
            ob = ob.__of__(self.portal)
            ob.getPhysicalPath = self.fakeGetPhysicalPath
            cat.indexMessage(ob)

        query = {}
        query['searchable_text'] = u'habilit�'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 0)

    def test_two_words(self):

        cat = self._getCatalog()

        for i in range(37):
            ob = self.getMailInstance(i)
            ob = ob.__of__(self.portal)
            ob.getPhysicalPath = self.fakeGetPhysicalPath
            cat.indexMessage(ob)

        query = {}
        query['searchable_text'] = u'enclosing message'
        res = cat.search(query_request=query)
        self.assertEquals(len(res), 1)


    def test_ZemanticInstanciation(self):

        ob = ZemanticMailCatalog()
        ob.add((URIRef(u'Tarek'), URIRef(u'likes'), URIRef(u'Pizza')))
        res = ob.query(Query(Any, u'<likes>', Any))
        res = list(res)
        self.assertEquals(len(res), 1)
        result = res[0]
        self.assertEquals(result.triple(), (u'Tarek', u'likes', u'Pizza'))

    def test_ZemanticSubject(self):
        ob = ZemanticMailCatalog()
        msg1_ref = URIRef(u'msgs/message1')

        ob.add((msg1_ref, URIRef(u'subject'), Literal(u'Pizza')))
        ob.add((msg1_ref, URIRef(u'body'), Literal(u'Pizzaaaa')))

        res = ob.query(Query(msg1_ref, Any, Any))
        res = list(res)
        self.assertEquals(len(res), 2)

    def test_ZemanticMessageAdapter(self):
        for i in range(37):
            message = self.getMailInstance(i)
            message = message.__of__(self.portal)
            message.getPhysicalPath = self.fakeGetPhysicalPath

            adapted_message = ZemanticMessageAdapter(message, None)
            tuple_ = adapted_message.threeTuples()

    def test_ZemanticMessageAdapterThreeTuples(self):

        message = self.getMailInstance(23)
        message = message.__of__(self.portal)
        message.getPhysicalPath = self.fakeGetPhysicalPath
        adapted_message = ZemanticMessageAdapter(message, None)
        tuples = adapted_message.threeTuples()
        self.assertEquals(len(tuples), 3)
        self.assertEquals(tuples[0], (u'nowere/my_message_2',
                                      u'from', u'bperson@dom.ain'))
        self.assertEquals(tuples[1], (u'nowere/my_message_2',
                                      u'to', u'aperson@dom.ain'))
        self.assertEquals(tuples[2], (u'nowere/my_message_2',
                                      u'subject', u'A subject'))


    def test_ZemanticMessageAdapterIndexerUnindexer(self):

        ob = ZemanticMailCatalog()
        messages = []
        for i in range(10):
            message = self.getMailInstanceT(i)
            message = message.__of__(self.portal)
            ob.indexMessage(message)
            messages.append(message)

        res = ob.query(Query(Any, Any, Any))
        self.assertEquals(len(list(res)),  46)

        subjects_ = list(ob.subjects())
        c_subjects_ = []
        for s_ in subjects_:
            if s_ not in c_subjects_:
                c_subjects_.append(s_)

        self.assertEquals(len(c_subjects_), 10)

        for message in messages:
            ob.unIndexMessage(message)

    def test_ZemanticMessageAdapterIndexerUnindexerWithQuestionMark(self):

        ob = ZemanticMailCatalog()
        messages = []

        message = self.getMailInstanceT(1)
        message = message.__of__(self.portal)
        message.setHeader('Subject', '????')

        ob.indexMessage(message)
        messages.append(message)
        ob.unIndexMessage(message)

        res = ob.query(Query(Any, Any, Any))
        self.assertEquals(len(list(res)),  0)

    def test_threading(self):
        ob = ZemanticMailCatalog()

        message1 = self.getMailInstanceT(1)
        message1 = message1.__of__(self.portal)
        message1.setHeader('Subject', 'message 1')
        message1.setHeader('message-id', '1')
        ob.indexMessage(message1)

        message2 = self.getMailInstanceT(1)
        message2 = message2.__of__(self.portal)
        message2.setHeader('Subject', 'message 2')
        message2.setHeader('message-id', '2')
        message2.setHeader('references', '1')
        ob.indexMessage(message2)

        message3 = self.getMailInstanceT(1)
        message3 = message3.__of__(self.portal)
        message3.setHeader('Subject', 'message 3')
        message3.setHeader('message-id', '3')
        message3.addHeader('references', '2')
        message3.addHeader('references', '1')
        # check headers
        refs = message3.getHeader('references')
        self.assertEquals(refs, ['2', '1'])

        ob.indexMessage(message3)

        # now we should have a clean thread semantically indexed
        msg1_uri = URIRef(unicode(message1.absolute_url()))
        res = ob.query(Query(msg1_uri, URIRef(u'thread'), Any))
        res = list(res)
        self.assertEquals(len(res), 0)

        msg2_uri = URIRef(unicode(message2.absolute_url()))
        res = ob.query(Query(msg2_uri, URIRef(u'thread'), Any))
        res = list(res)
        self.assertEquals(len(res), 1)

        msg3_uri = URIRef(unicode(message3.absolute_url()))
        res = ob.query(Query(msg3_uri, URIRef(u'thread'), Any))
        res = list(res)
        self.assertEquals(len(res), 2)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailSearchTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailsearch'),
        ))

