##############################################################################
#
# Copyright (c) 2004-1005 Michel Pelletier and Contributors
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import unittest

from rdflib.URIRef import URIRef
from rdflib.Literal import Literal

from zope.testing.doctestunit import DocTestSuite

from zemantic.triplestore import TripleStore
from zemantic.query import UnionChain
from zemantic.public import *

class QueryTestCase(unittest.TestCase):

    def _getSampleCatalog(self):
        store = TripleStore()

        store.add((URIRef(u'Tarek'), URIRef(u'likes'), URIRef(u'pizza')))
        store.add((URIRef(u'Bob'), URIRef(u'likes'), URIRef(u'cheese')))
        store.add((URIRef(u'Bob'), URIRef(u'hates'), URIRef(u'pizza')))
        store.add((URIRef(u'Robert'), URIRef(u'likes'), URIRef(u'pizza')))
        store.add((URIRef(u'Marie'), URIRef(u'likes'), URIRef(u'cheese')))
        store.add((URIRef(u'Tarek'), URIRef(u'likes'), URIRef(u'cheese')))
        store.add((URIRef(u'Michel'), URIRef(u'likes'), URIRef(u'cheese')))
        store.add((URIRef(u'Michel'), URIRef(u'likes'), URIRef(u'pizza')))

        return store

    def _getSampleCatalog2(self):
        store = TripleStore()

        store.add((URIRef(u'Tarek'), URIRef(u'likes'), Literal(u'pizza')))
        store.add((URIRef(u'Bob'), URIRef(u'likes'), Literal(u'cheese')))
        store.add((URIRef(u'Bob'), URIRef(u'hates'), Literal(u'pizza')))
        store.add((URIRef(u'Robert'), URIRef(u'likes'), Literal(u'pizza')))
        store.add((URIRef(u'Marie'), URIRef(u'likes'), Literal(u'cheese')))
        store.add((URIRef(u'Tarek'), URIRef(u'likes'), Literal(u'cheese')))
        store.add((URIRef(u'Michel'), URIRef(u'likes'), Literal(u'cheese')))
        store.add((URIRef(u'Michel'), URIRef(u'likes'), Literal(u'pizza')))

        return store

    def stest_repr(self):
        ob = self._getSampleCatalog()
        repr_ = ob.__repr__()
        self.assertNotEquals(repr_, None)

    def stest_simpleQueries(self):
        ob = self._getSampleCatalog()

        res = ob.query(Query(Any, Any, Any))
        res = list(res)
        self.assertEquals(len(res), 8)

        res = ob.query(Query(Any, u'<likes>', Any))
        res = list(res)
        self.assertEquals(len(res), 7)

        res = ob.query(Query(Any, u'<hates>', Any))
        res = list(res)
        self.assertEquals(len(res), 1)

        res = ob.query(Query(u'<Bob>', Any, Any))
        res = list(res)
        self.assertEquals(len(res), 2)

        res = ob.query(Query(u'<Bob>', Any, u'<cheese>'))
        res = list(res)
        self.assertEquals(len(res), 1)

        res = ob.query(Query(u'<Bob>',  u'<likes>', u'<cheese>'))
        res = list(res)
        self.assertEquals(len(res), 1)


        res = ob.query(Query(u'<Bob>',  u'<hates>', u'<cheese>'))
        res = list(res)
        self.assertEquals(len(res), 0)

    def stest_unionQueries(self):
        ob = self._getSampleCatalog()

        # testing with one query
        q1 = Query(Any, Any, Any)
        direct = ob.query(q1)
        direct = list(direct)

        q1 = UnionChain(q1)

        self.assertNotEquals(q1, None)

        res = ob.query(q1)
        self.assertNotEquals(res, None)
        res = list(res)

        self.assertEquals(len(res), len(direct))

        # testing with two queries : what bob likes or hates
        q1 = Query(u'<Bob>',  u'<likes>', Any)
        q2 = Query(u'<Bob>',  u'<hates>', Any)

        q1_and_q2 = UnionChain(q1, q2)
        self.assertNotEquals(q1_and_q2, None)

        res = ob.query(q1_and_q2)
        self.assertNotEquals(res, None)
        res = list(res)
        self.assertEquals(len(res), 2)

        # testing empty query
        res = ob.query(UnionChain())
        res = list(res)
        self.assertEquals(len(res), 0)

    def stest_complexQueries(self):

        ob = self._getSampleCatalog()

        # testing with two queries : what bob likes or hates
        q1 = Query(u'<Bob>',  u'<likes>', Any)
        q2 = Query(u'<Bob>',  u'<hates>', Any)

        q1_and_q2 = UnionChain(q1, q2)
        self.assertNotEquals(q1_and_q2, None)

        res = ob.query(q1_and_q2)
        self.assertNotEquals(res, None)
        res = list(res)
        self.assertEquals(len(res), 2)

        # people who likes cheese *or* pizza
        q1 = Query(Any,  u'<likes>', u'<cheese>')
        q2 = Query(Any,  u'<likes>', u'<pizza>')

        q1_or_q2 = UnionChain(q1, q2)
        res = ob.query(q1_or_q2)
        res = list(res)
        self.assertEquals(len(res), 7)

        # what bob likes and hates *or* people who likes cheese or pizza
        q1_or_q2 = UnionChain(q1_and_q2, q1_or_q2)
        res = ob.query(q1_or_q2)
        res = list(res)
        self.assertEquals(len(res), 8)

    def test_indexing(self):
        ob = self._getSampleCatalog2()

        # full value
        query = Query(u'<Bob>',  u'<hates>', u'"pizza"')
        res = ob.query(query)
        res = list(res)
        self.assertEquals(len(res), 1)

        query = Query(u'<Bob>',  u'<hates>', u'"piz*"')
        res = ob.query(query)
        res = list(res)
        self.assertEquals(len(res), 1)


        query = UnionChain(Query(Any,  u'<hates>', u'"p*"'))
        res = ob.query(query)
        res = list(res)
        self.assertEquals(len(res), 1)

        query = Query(u'<Bob>',  u'<hates>', u'"aezlpfhkezapihaz"')
        res = ob.query(query)
        res = list(res)
        self.assertEquals(len(res), 0)


def test_suite():
    return unittest.TestSuite((unittest.makeSuite(QueryTestCase),
                               DocTestSuite('zemantic.query')))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
