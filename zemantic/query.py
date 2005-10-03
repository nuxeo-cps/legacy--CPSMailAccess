##############################################################################
#
# Copyright (c) 2004-1005 Michel Pelletier
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

"""
Queries are any callable object (like a function) that query the
triple store.  These are technically not agents, just agent helpers.
QueryChains are queries that chains other queries in various ways
(union, intersection).

"""

__rdf_description__ = '''\
<rdf:RDF xmlns="http://web.resource.org/cc/"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<Work rdf:about="http://zemantic.org/zemantic/query.py"
  dc:title="zemantic.query"
  dc:date="2005"
  dc:description="Queries and stock query logic.">
    <dc:creator>
            <Agent dc:title="Michel Pelletier"/>
    </dc:creator>
    <dc:rights>
            <Agent dc:title="Michel Pelletier"/>
    </dc:rights>
    <license rdf:resource="http://zemantic.org/LICENSE.txt/"/>
</Work>
</rdf:RDF>
'''

from types import UnicodeType, NoneType, TupleType
from Products.CPSMailAccess.zemantic.rdflib.Identifier import Identifier
from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal

from zope.interface import implements
from interfaces import IQuery, IQueryChain, IIdentifier
from result import Result

import BTrees
from BTrees.OOBTree import OOSet as Set

class QueryException(Exception):

    """ Thrown by a query to indicate a query exception."""

class BadQueryException(QueryException):

    """ Throw by a query to indicate a query is malformed."""

class Query(object):

    """ A generic query logic class.  A straightforward interface to
    zemantic.TripleStore.triples() with support for inner queries.

    This class does simple triple pattern queries on a catalog.  If an
    identifier term is a nested query (3-tuple or IQuery implementor)
    then it performs the inner query first, applying each of the
    results of the inner query to the outer query.

    When called, returns a result generator or None (no results) or
    throws an exception.

      >>> from triplestore import TripleStore
      >>> c = TripleStore()
      >>> q = Query(None, None, None)
      >>> c.query(q) is not None
      True

    """
    implements(IQuery)

    inner = False

    def __init__(self, subject=None, predicate=None, object=None, context=None):
        s, p, o, c = subject, predicate, object, context

        ts = type(s)
        if ts is UnicodeType:
            if s.startswith("<"):
                s = URIRef(s[1:-1])
            elif s.startswith('"'):
                raise ValueError, "Literals cannot be subjects."
            elif s.startswith('_'):
                s = BNode(s)
            else:
                raise ValueError, "Unicode subject term %s is not a well formed N3 identifier" % s
        elif ts is TupleType or IQuery.providedBy(s):
            self.inner = True
        elif ts is NoneType or IIdentifier.providedBy(s):
            pass # it's cool
        else:
            raise ValueError, "Subject term must be None unicode, IIdentifier, IQuery or 3-tuple."


        tp = type(p)
        if tp is UnicodeType:
            if p.startswith("<"):
                p = URIRef(p[1:-1])
            elif p.startswith('"'):
                raise ValueError, "Literals cannot be predicates."
            elif p.startswith('_'):
                raise ValueError, "BNodes cannot be predicates."
            else:
                raise ValueError, "Unicode predicate term %s is not a well formed N3 identifier" % p
        elif tp is TupleType or IQuery.providedBy(p):
            self.inner = True
        elif tp is NoneType or IIdentifier.providedBy(p):
            pass # it's cool
        else:
            raise ValueError, "Subject term must be None unicode, IIdentifier, IQuery or 3-tuple."


        to = type(o)
        if to is UnicodeType:
            if o.startswith("<"):
                o = URIRef(o[1:-1])
            elif o.startswith('"'):
                o = Literal(o[1:-1])
            elif o.startswith('_'):
                o = BNode(o)
            else:
                raise ValueError, "Unicode object term %s is not a well formed N3 identifier" % o

        elif to is TupleType or IQuery.providedBy(o):
            self.inner = True
        elif to is NoneType or IIdentifier.providedBy(o):
            pass # it's cool
        else:
            raise ValueError, "Object term must be None, unicode, IIdentifier, IQuery or 3-tuple."


        tc = type(c)
        if tc is UnicodeType:
            if c.startswith("<"):
                c = URIRef(c[1:-1])
            elif c.startswith('"'):
                raise ValueError, "Literals cannot be contexts."
            elif c.startswith('_'):
                raise ValueError, "BNodes cannot be contexts."
            else:
                raise ValueError, "Unicode context term %s is not a well formed N3 identifier" % o

        elif tc is TupleType or IQuery.providedBy(c):
            self.inner = True
        elif tc is NoneType or IIdentifier.providedBy(c):
            pass # it's cool
        else:
            raise ValueError, "Context term must be None, unicode, IIdentifier, IQuery or 3-tuple."

        self.s = s
        self.p = p
        self.o = o
        self.c = c

    def __call__(self, store, max_results=100):

        # common path, no inner queries
        try:
            if not self.inner:
                stored = store.triples((self.s, self.p, self.o), self.c)
                i = 1
                for result in stored:
                    if i > max_results:
                        break
                    else:
                        i+=1
                    yield Result(result)
            else:

                # inner query logic here is definitely _not_ optimized, I
                # imagine there is all kinds of query optimization and
                # algebraic reduction that can be applied but that's not
                # the point, users will have to be aware of the fact that
                # broad inner queries can significantly impact
                # performance.

                # first, determine inner subjects

                if self.s is None:
                    isresult = []
                    for s in store.uniqueSubjects():
                        isresult.append(Result((s, None, None)))

                elif type(self.s) is TupleType or IQuery.providedBy(self.s):
                    if type(self.s) is TupleType:
                        q = apply(Query, self.s)
                    else:
                        q = self.s
                    isresult = store.query(q)
                else:
                    isresult = [Result((self.s, None, None))]

                # determine inner predicates

                if self.p is None:
                    ipresult = []
                    for p in store.uniquePredicates():
                        ipresult.append(Result((None, p, None)))

                elif type(self.p) is TupleType or IQuery.providedBy(self.p):
                    if type(self.p) is TupleType:
                        q = apply(Query, self.p)
                    else:
                        q = self.p
                    ipresult = store.query(q)

                else:
                    ipresult = [Result((None, self.p, None))]

                # determine inner objects

                if self.o is None:
                    ioresult = []
                    for o in store.uniqueObjects():
                        ioresult.append(Result((None, None, o)))

                elif type(self.o) is TupleType or IQuery.providedBy(self.o):
                    if type(self.o) is TupleType:
                        q = apply(Query, self.o)
                    else:
                        q = self.o
                    ioresult = store.query(q)

                else:
                    ioresult = [Result((None, None, self.o))]

                # put it all together

                for sresult in isresult:
                    for presult in ipresult:
                        for oresult in ioresult:
                            yield Result((sresult.subject, presult.predicate, oresult.object))
        except KeyError:
            raise StopIteration

    def __repr__(self):
        return "<Query: %s, %s, %s>" % (self.s, self.p, self.o)

class QueryChain(Query):

    """ Abstract class to combine a "chain" of queries into one result
    set.  QueryChains are themselves Queries, and can be nested. """

    implements(IQueryChain)

    _queries = None

    def __init__(self, *queries):
        Query.__init__(self)
        self._queries = []
        for x in queries:
            self.add(x)

    def add(self, query):
        """ Append a query onto the chain """
        self._queries.append(query)

    def getQueries(self):
        """ Return the chain of queries. """
        return self._queries

    def __call__(self, store):
        """ Eval a query chain with given args.  Queries throw
        QueryException to stop chain procesing and declare failure."""

        raise NotImplementedError



class UnionChain(QueryChain):
    """
    Take the union of a chain of queries.

      >>> from triplestore import TripleStore
      >>> c = TripleStore()
      >>> u = UnionChain(c, Query())
      >>> u = UnionChain(c, Query(), Query())

    """
    def _union(self, x, y):
        """ Slow but obviously correct Python implementations of basic ops """
        result = list(x)
        for e in y:
            found = False
            for item in result:
                if e.triple() == item.triple():
                    found = True
                    break
            if not found:
                result.append(e)
        result.sort()
        return result

    def __call__(self, store, max_results=100):
        if len(self._queries) == 0:
            pass
        else:
            results = []
            for query in self._queries:
                results = self._union(results, (list(query(store))))
                #results = BTrees.OOBTree.union(results, Set(list(query(store))))
            i = 0
            for result in results:
                if i >= max_results:
                    break
                else:
                    i += 1
                yield result

class IntersectionChain(QueryChain):
    """
    Take the intersection of a chain of queries.

      >>> from triplestore import TripleStore
      >>> c = TripleStore()
      >>> i = IntersectionChain(c, Query())
      >>> i = IntersectionChain(c, Query(), Query())

    XXX this is broken for now
    """

    def __call__(self, store):
        if len(self._queries) == 0:
            pass
        elif len(self._queries) == 1:
            results = self._queries[0](store)
            for result in results:
                yield result
        else:
            results = Set(list(self._queries[0](store)))
            for query in self._queries[1:]:
                results = BTrees.OOBTree.intersection(results, Set(list(query(store))))
            for result in results:
                yield result
