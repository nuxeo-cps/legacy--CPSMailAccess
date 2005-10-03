from __future__ import generators

import tempfile, shutil, os
from threading import Lock

from urlparse import urlparse, urljoin, urldefrag
from urllib import pathname2url, url2pathname

from Products.CPSMailAccess.zemantic.rdflib import RDF, RDFS
from Products.CPSMailAccess.zemantic.rdflib.URLInputSource import URLInputSource

from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal

from Products.CPSMailAccess.zemantic.rdflib.util import first

from Products.CPSMailAccess.zemantic.rdflib.syntax.serializer import SerializationDispatcher
from Products.CPSMailAccess.zemantic.rdflib.syntax.parser import ParserDispatcher

from Products.CPSMailAccess.zemantic.rdflib.exceptions import SubjectTypeError
from Products.CPSMailAccess.zemantic.rdflib.exceptions import PredicateTypeError
from Products.CPSMailAccess.zemantic.rdflib.exceptions import ObjectTypeError


def check_subject(s):
    if not (isinstance(s, URIRef) or isinstance(s, BNode)):
        import pdb;pdb.set_trace()
        raise SubjectTypeError(s)

def check_predicate(p):
    if not isinstance(p, URIRef):
        import pdb;pdb.set_trace()
        raise PredicateTypeError(p)

def check_object(o):
    if not (isinstance(o, URIRef) or \
       isinstance(o, Literal) or \
       isinstance(o, BNode)):
        import pdb;pdb.set_trace()
        raise ObjectTypeError(o)



class Store(object):
    """
    Abstract Class
    """

    def __init__(self, backend):
        super(Store, self).__init__()
        self.backend = backend
        self.ns_prefix_map = {}
        self.prefix_ns_map = {}
        self.prefix_mapping("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.prefix_mapping("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        self.serialize = SerializationDispatcher(self)
        self.parse = ParserDispatcher(self)
        self.__save_lock = Lock()

    def open(self, path):
        self.backend.open(path)

    def close(self):
        self.backend.close()

    def absolutize(self, uri, defrag=1):
        # TODO: make base settable
        base = urljoin("file:", pathname2url(os.getcwd()))
        uri = urljoin("%s/" % base, uri)
        if defrag:
            uri, frag = urldefrag(uri)
        return URIRef(uri)

    def load(self, location, format="xml", publicID=None):
        source = URLInputSource(self.absolutize(location))
        if publicID:
            source.setPublicId(publicID)
        self.parse(source, format=format)

    def save(self, location, format="xml"):
        try:
            self.__save_lock.acquire()

            scheme, netloc, path, params, query, fragment = urlparse(location)
            if netloc!="":
                print "WARNING: not saving as location is not a local file reference"
                return

            name = tempfile.mktemp()
            stream = open(name, 'wb')
            self.serialize(format=format, stream=stream)
            stream.close()

            if hasattr(shutil,"move"):
                shutil.move(name, path)
            else:
                shutil.copy(name, path)
                os.remove(name)

        finally:
            self.__save_lock.release()

    def prefix_mapping(self, prefix, namespace):
        map = self.ns_prefix_map
        map[namespace] = prefix

    def label(self, subject, default=''):
        for s, p, o in self.triples((subject, RDFS.label, None)):
            return o
        return default

    def comment(self, subject, default=''):
        for s, p, o in self.triples((subject, RDFS.comment, None)):
            return o
        return default

    def items(self, list):
        while list:
            item = first(self.objects(list, RDF.first))
            if item:
                yield item
            list = first(self.objects(list, RDF.rest))

    def __iter__(self):
        return self.triples((None, None, None))

    def __contains__(self, (subject, predicate, object)):
        for triple in self.triples((subject, predicate, object)):
            return 1
        return 0

    def __len__(self):
        return self.backend.__len__()

    def __eq__(self, other):
        # Note: this is not a test of isomorphism, but rather exact
        # equality.
        if not other or len(self)!=len(other):
            return 0
        for s, p, o in self:
            if not (s, p, o) in other:
                return 0
        for s, p, o in other:
            if not (s, p, o) in self:
                return 0
        return 1

    def __iadd__(self, other):
        for triple in other:
            self.backend.add(triple)
        return self

    def __isub__(self, other):
        for triple in other:
            self.backend.remove(triple)
        return self

    def subjects(self, predicate=None, object=None):
        for s, p, o in self.triples((None, predicate, object)):
            yield s

    def predicates(self, subject=None, object=None):
        for s, p, o in self.triples((subject, None, object)):
            yield p

    def objects(self, subject=None, predicate=None):
        for s, p, o in self.triples((subject, predicate, None)):
            yield o

    def subject_predicates(self, object=None):
        for s, p, o in self.triples((None, None, object)):
            yield s, p

    def subject_objects(self, predicate=None):
        for s, p, o in self.triples((None, predicate, None)):
            yield s, o

    def predicate_objects(self, subject=None):
        for s, p, o in self.triples((subject, None, None)):
            yield p, o

    def transitive_objects(self, subject, property, remember=None):
        if remember==None:
            remember = {}
        if not subject in remember:
            remember[subject] = 1
            yield subject
            for object in self.objects(subject, property):
                for o in self.transitive_objects(object, property, remember):
                    yield o

    def transitive_subjects(self, predicate, object, remember=None):
        if remember==None:
            remember = {}
        if not object in remember:
            remember[object] = 1
            yield object
            for subject in self.subjects(predicate, object):
                for s in self.transitive_subjects(predicate, subject, remember):
                    yield s

