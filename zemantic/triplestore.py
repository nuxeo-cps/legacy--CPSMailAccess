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

__rdf_description__ = '''\
<rdf:RDF xmlns="http://web.resource.org/cc/"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
# <Work rdf:about="http://zemantic.org/zemantic/triplestore.py"
  dc:title="zemantic.triplestore"
  dc:date="2005"
  dc:description="Triple store catalogs.">
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
from persistent import Persistent
from persistent.dict import PersistentDict

from rdflib.TripleStore import TripleStore as rdflibTripleStore     # not pickleable
from rdflib.URIRef import URIRef
from rdflib.BNode import BNode
from rdflib.Literal import Literal
from rdflib.Identifier import Identifier

from query import Query
from result import Result
from lib.ZODBBackend import ZODBBackend
from lib.IOZODBBackend import IOZODBBackend
from lib.IOZODBTextIndexBackend import IOZODBTextIndexBackend
from interfaces import ITripleStore
from events import afterAdd, beforeRemove

from zope.interface import implements
from zope.interface.verify import verifyClass
from zope.app.size.interfaces import ISized

class TripleStore(Persistent):
    """
    A semantic zemantic.  A wrapper around a persistent rdflib backend
    that is used to construct an rdflib triplestore.

      >>> c = TripleStore()
      >>> ITripleStore.providedBy(c)
      True
      >>> verifyClass(ITripleStore, TripleStore)
      True

    See Zontology class doctests for more tests.

    """

    implements(ITripleStore)

    _v_store = backend = __parent__ = __name__ = None
    notify = False

    def __init__(self, backend=None):
        if backend is None:
            backend = IOZODBTextIndexBackend()
        self.backend = backend

    def clear(self, backend=None):
        """ Clear zemantic. """
        if backend is None:
            backend = IOZODBTextIndexBackend()
        self.backend = backend
        self._v_store = rdflibTripleStore(backend=backend)

    def notifyOn(self):
        """
        Turn on event notification.
        """
        self.notify = True

    def notifyOff(self):
        self.notify = False

    def getStore(self):
        """
        Returns a TripleStore wrapping the semantic storage.
        """
        if self._v_store is None:
            self._v_store = rdflibTripleStore(backend=self.backend)  # not pickleable
        return self._v_store

    store = property(getStore)

    def parse(self, rdf, format="xml"):
        """
        Parse RDF information.  The optional"format" argument can be "xml"
        (the default) or "nt".  Note, I have not tested nt yet.  Also a
        bug in rdflib requires you pass a file like object.

        First, test the default (XML) parser.

        >>> from StringIO import StringIO
        >>> faux_rdf_file = StringIO(FAUX_RDF_FILE)
        >>> c = TripleStore()
        >>> len(allTriples(c))
        0
        >>> c.parse(faux_rdf_file)
        >>> len(allTriples(c))
        1
        >>> allTriples(c)[0][0]
        u'http://zemantic.org/zemantic/zemantic.py'
        >>> allTriples(c)[0][1]
        u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
        >>> allTriples(c)[0][2]
        u'http://web.resource.org/cc/Work'

        Then, test the explicit version.

        >>> faux_rdf_file = StringIO(FAUX_RDF_FILE)
        >>> c = TripleStore()
        >>> len(allTriples(c))
        0
        >>> c.parse(faux_rdf_file, 'xml')
        >>> len(allTriples(c))
        1
        >>> allTriples(c)[0][0]
        u'http://zemantic.org/zemantic/zemantic.py'
        >>> allTriples(c)[0][1]
        u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
        >>> allTriples(c)[0][2]
        u'http://web.resource.org/cc/Work'

        Now, test the NT version.

        >>> faux_nt_file = StringIO(FAUX_NT_FILE)
        >>> c = TripleStore()
        >>> len(allTriples(c))
        0
        >>> c.parse(faux_nt_file, 'nt')
        >>> len(allTriples(c))
        1
        >>> allTriples(c)[0][0]
        u'http://zemantic.org/zemantic/zemantic.py'
        >>> allTriples(c)[0][1]
        u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
        >>> allTriples(c)[0][2]
        u'http://web.resource.org/cc/Work'

        """
        # Could we get a list of the parsed statements back from rdflib?
        # If so, then we could call 'afterAdd' with them.
        self.store.parse(rdf, format=format)

    def add(self, (subject, predicate, object)):
        """
        Add a triple to the storage.

        >>> c = TripleStore()
        >>> len(allTriples(c))
        0
        >>> from rdflib.URIRef import URIRef
        >>> from rdflib.URIRef import Literal
        >>> c.add((URIRef('http://zope.org'), \
                    URIRef('http://purl.org/dc/1.1/#Title'), \
                    Literal('Zope Community Site')))
        >>> len(allTriples(c))
        1
        >>> allTriples(c)[0][0]
        u'http://zope.org'
        >>> allTriples(c)[0][1]
        u'http://purl.org/dc/1.1/#Title'
        >>> allTriples(c)[0][2]
        u'Zope Community Site'
        """
        t = (subject, predicate, object)
        self.store.add(t)

        if self.notify:
            afterAdd(t)

    def addTriples(self, statements):
        """
        Add a set of statments to the store.

        >>> c = TripleStore()
        >>> len(allTriples(c))
        0
        >>> from rdflib.URIRef import URIRef
        >>> from rdflib.URIRef import Literal
        >>> c.addTriples( \
               [(URIRef('http://zope.org'), \
                 URIRef('http://purl.org/dc/1.1/#Title'), \
                 Literal('Zope Community Site')), \
                (URIRef('http://zope.org'), \
                 URIRef('http://purl.org/dc/1.1/#Description'), \
                 Literal('Site for downloading Zope and contributed add-ons')),\
               ])
        >>> len(allTriples(c))
        2
        >>> allTriples(c)[0][0]
        u'http://zope.org'
        >>> allTriples(c)[1][1]
        u'http://purl.org/dc/1.1/#Title'
        >>> allTriples(c)[1][2]
        u'Zope Community Site'
        """
        # Should 'afterAdd' take either one or many statements?  If
        # so, then we could call it only once.
        for statement in statements:
            self.add(statement)

    def remove(self, (subject, predicate, object)):
        """
        Remove a triple from the storage.

        >>> c = TripleStore()
        >>> from rdflib.URIRef import URIRef
        >>> from rdflib.URIRef import Literal
        >>> c.add((URIRef('http://zope.org'), \
                    URIRef('http://purl.org/dc/1.1/#Title'), \
                    Literal('Zope Community Site')))
        >>> c.add((URIRef('http://www.zemantic.org'), \
                    URIRef('http://purl.org/dc/1.1/#Title'), \
                    Literal('Zemantic Web Site')))
        >>> len(allTriples(c))
        2
        >>> c.remove((URIRef('http://zope.org'), \
                      URIRef('http://purl.org/dc/1.1/#Title'), \
                      Literal('Zope Community Site')))
        >>> len(allTriples(c))
        1
        >>> allTriples(c)[0][0]
        u'http://www.zemantic.org'
        """
        t = (subject, predicate, object)
        if self.notify:
            beforeRemove(t)

        self.store.remove(t)

    def triples(self, (subject, predicate, object), *args):
        """
        Query the triple storage.  The argument is a triple pattern
        which can contain a valid value or None to indicate any value
        is desired.
        """

        for triple in self.store.triples((subject, predicate, object)):
            yield triple

    def query(self, q):
        """
        Query zemantic with a query object.
        """

        return q(self)

    # no need to test the rest, they're all based on triples()

    def subjects(self, predicate=None, object=None):
        return self.store.subjects(predicate, object)

    def predicates(self, subject=None, object=None):
        return self.store.predicates(subject, object)

    def objects(self, subject=None, predicate=None):
        return self.store.objects(subject, predicate)

    def subject_predicates(self, object=None):
        return self.store.subject_predicates(object)

    def subject_objects(self, predicate=None):
        return self.store.subject_objects(predicate)

    def predicate_objects(self, subject=None):
        return self.store.predicate_objects(subject)

    def transitive_objects(self, subject, property, remember=None):
        return self.store.transitive_objects(subject, property, remember)

    def transitive_subjects(self, predicate, object, remember=None):
        return self.store.transitive_subjects(predicate, object, remember)

    def uniqueSubjects(self):
        return self.backend.uniqueSubjects()

    def uniquePredicates(self):
        return self.backend.uniquePredicates()

    def uniqueObjects(self):
        return self.backend.uniqueObjects()

    def rdfxml(self):
        return self.store.serialize()

    def rdfnt(self):
        return self.store.serialize("nt")

    def __len__(self):
        return len(self.store)


class TripleStoreSized(object):
    implements(ISized)

    def __init__(self, zemantic):
        self._zemantic = zemantic

    def sizeForSorting(self):
        return ('item', len(self._zemantic))

    def sizeForDisplay(self):
        return str(len(self._zemantic)) + ' triples'
