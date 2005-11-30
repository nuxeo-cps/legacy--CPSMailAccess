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
from Products.CPSMailAccess.mailsearch \
    import ZemanticMailCatalog, ZemanticMessageAdapter, intersection, union

from Testing.ZopeTestCase import installProduct
from basetestcase import MailTestCase
from Testing.ZopeTestCase import installProduct
from mailmessage import MailMessage

from zemantic.public import *
from zemantic.query import Query
from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal

class MailSearchTestCase(MailTestCase):

    count = 0
    def fakeGetPhysicalPath(self):
        self.count += 1
        return ('', 'nowere/my_message_' + str(self.count))

    def sameGetPhysicalPath(self):
        return ('', 'nowere/i_am_not_moving')

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

    def test_ZemanticMessageAdapterWithRelations(self):
        for i in range(37):
            message = self.getMailInstance(i)
            message = message.__of__(self.portal)
            message.getPhysicalPath = self.fakeGetPhysicalPath

            adapted_message = ZemanticMessageAdapter(message, None)
            tuple_ = adapted_message.threeTuples(index_relations=True)

    def test_ZemanticMessageAdapterThreeTuples(self):

        message = self.getMailInstance(23)
        message = message.__of__(self.portal)
        message.getPhysicalPath = self.fakeGetPhysicalPath
        adapted_message = ZemanticMessageAdapter(message, None)
        tuples = adapted_message.threeTuples()
        self.assertEquals(len(tuples), 4)
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
        self.assertEquals(len(list(res)),  56)

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
        message1.setHeader('message-id', '<1>')
        ob.indexMessage(message1)

        message2 = self.getMailInstanceT(1)
        message2 = message2.__of__(self.portal)
        message2.setHeader('Subject', 'message 2')
        message2.setHeader('message-id', '<2>')
        message2.setHeader('references', '<1>')
        ob.indexMessage(message2)

        message3 = self.getMailInstanceT(1)
        message3 = message3.__of__(self.portal)
        message3.setHeader('Subject', 'message 3')
        message3.setHeader('message-id', '<3>')
        message3.addHeader('references', '<2>')
        message3.addHeader('references', '<1>')
        # check headers
        refs = message3.getHeader('references')
        self.assertEquals(refs, ['<2>', '<1>'])

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

        # testing back references
        res = ob.query(Query(msg1_uri, URIRef(u'back-thread'), Any))
        res = list(res)
        self.assertEquals(len(res), 2)

    def test_clear(self):
        ob = ZemanticMailCatalog()

        message1 = self.getMailInstanceT(1)
        message1 = message1.__of__(self.portal)
        message1.setHeader('Subject', 'message 1')
        message1.setHeader('message-id', '1')
        ob.indexMessage(message1)

        res = ob.query(Query(Any, Any, Any))
        res = list(res)
        self.assertEquals(len(res), 7)

        ob.clear()

        res = ob.query(Query(Any, Any, Any))
        res = list(res)
        self.assertEquals(len(res), 0)

    def test_intersection(self):
        one = ['a', 'a', 'b']
        two = ['b', 'c', 'b', 'y']
        inter = intersection(one, two)
        self.assertEquals(inter, ['b'])

    def test_union(self):
        one = ['a', 'a', 'b']
        two = ['b', 'c', 'b', 'y']
        un = union(one, two)
        un.sort()
        self.assertEquals(un, ['a', 'b', 'c', 'y'])

        one = ['a', 'a', 'b']
        un = union(one)
        un.sort()
        self.assertEquals(un, ['a', 'b'])

    def test_folder_indexing(self):

        box = self._getMailBox()
        folder = box._addFolder('fol', 'INBOX.fol')
        msg = folder._addMessage('1', 'INBOX.fol.1')

        orphan_message = self.getMailInstanceT(1)

        ob = ZemanticMailCatalog()

        ob.indexMessage(msg)
        ob.indexMessage(orphan_message)

        res = ob.query(Query(Any, URIRef(u'folder'), Any))
        self.assertEquals(len(list(res)), 2)

        res = ob.query(Query(Any, URIRef(u'folder'), URIRef(u'INBOX.fol')))
        self.assertEquals(len(list(res)), 1)

    def test_normalizing(self):

        message = self.getMailInstance(23)
        message = message.__of__(self.portal)

        message.setHeader('subject', 'éééééééé')

        message.getPhysicalPath = self.fakeGetPhysicalPath
        adapted_message = ZemanticMessageAdapter(message, None)

        self.assertEquals(adapted_message._normalize(u'éééé'), u'eeee')
        self.assertEquals(adapted_message._normalize('éééé'), u'eeee')

        tuple_ = adapted_message.threeTuples()
        predicates = [predicate for subject, object, predicate in tuple_]
        predicates.sort()

        self.assertEquals(predicates, [u'_#_orphan_#_', u'aperson@dom.ain',
                                       u'bperson@dom.ain', u'eeeeeeee'])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailSearchTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailsearch'),
        ))

