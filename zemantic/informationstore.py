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
<Work rdf:about="http://zemantic.org/zemantic/informationstore.py"
  dc:title="zemantic.informationstore"
  dc:date="2005"
  dc:description="Information store catalogs.">
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

from Products.CPSMailAccess.zemantic.rdflib.InformationStore import InformationStore as rdflibInformationStore     # not pickleable
from Products.CPSMailAccess.zemantic.rdflib.InformationStore import ContextBackend
from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal
from Products.CPSMailAccess.zemantic.rdflib.Identifier import Identifier
import urllib

from query import Query
from result import Result
from triplestore import TripleStore
from lib.ZODBBackend import ZODBBackend
from lib.IOZODBContextBackend import IOZODBContextBackend
from interfaces import ITripleStore, IInformationStore, IContext
from events import afterAdd, beforeRemove

from zope.interface import implements
from zope.interface.verify import verifyClass
from zope.app.size.interfaces import ISized

class InformationStore(Persistent):
    """
    A wrapper around a persistent rdflib backend that is used to
    construct an rdflib informationstore.

      >>> c = InformationStore()
      >>> IInformationStore.providedBy(c)
      True
      >>> verifyClass(IInformationStore, InformationStore)
      True

    """

    implements(IInformationStore)

    _v_store = backend = __parent__ = __name__ = None
    notify = False

    def __init__(self, backend=None):
        if backend is None:
            backend = IOZODBContextBackend()
        self.backend = backend

    def clear(self):
        """
        Clear information store.
        """
        for context in self.getContexts():
            for t in self.triples((None, None, None), context):
                self.remove(t, context)

    def notifyOn(self):
        """
        Turn on event notification.
        """
        self.notify = True

    def notifyOff(self):
        self.notify = False

    def getStore(self):
        """
        Returns a InformationStore wrapping the semantic storage.
        """
        if self._v_store is None:
            self._v_store = rdflibInformationStore(backend=self.backend)  # not pickleable
        return self._v_store

    store = property(getStore)

    def parse(self, rdf, context, format="xml"):
        """
        Parse RDF information.  The optional"format" argument can be "xml"
        (the default) or "nt".  Note, I have not tested nt yet.  Also a
        bug in rdflib requires you pass a file like object.
        """
        self.getContext(context).parse(rdf, format=format)

    def add(self, (subject, predicate, object), context):
        """
        Add a triple to the storage.
        """
        t = (subject, predicate, object)
        self.store.add(t, context)

        if self.notify:
            afterAdd(t)

    def remove(self, (subject, predicate, object), context):
        """
        Add a triple to the storage.
        """
        t = (subject, predicate, object)
        if self.notify:
            beforeRemove(t)

        self.store.remove(t, context)

    def triples(self, (subject, predicate, object), context, *args):
        """
        Query the triple storage.  The argument is a triple pattern
        which can contain a valid value or None to indicate any value
        is desired.
        """

        for triple in self.store.triples((subject, predicate, object), context):
            yield triple

    def query(self, q):
        """
        Query zemantic with a query object.
        """
        return q(self)

    def getContext(self, context):
        return TripleStore(backend=ContextBackend(self.store, context))

    def getContexts(self):
        for context in self.store.contexts():
            yield self.getContext(context)

    def __len__(self):
        return len(list(self.store.contexts()))

class InformationStoreSized(object):
    implements(ISized)

    def __init__(self, istore):
        self._istore = istore

    def sizeForSorting(self):
        return ('item', len(self._istore))

    def sizeForDisplay(self):
        return str(len(self._istore)) + ' triples'
