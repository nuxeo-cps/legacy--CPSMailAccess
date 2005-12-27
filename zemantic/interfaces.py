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
<Work rdf:about="http://zemantic.org/zemantic/interfaces.py"
  dc:title="zemantic.interfaces"
  dc:date="2005"
  dc:description="Interface definitions for Zemantic components.">
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

from zope.interface import Interface, classImplements, Attribute, Invalid

class IRDFThreeTuples(Interface):
    """ Interface for a component that wants to generate RDF XML."""

    def threeTuples():
        """ Return a sequence of three-tuples describing of this component.

        o All values must be unicode.

        o URIs must be contained within <>.

        o Literals must be contained within "" (*inside* the Unicode string!).

        E.g.:

          [('<http://example.com/path/to/object>',
            '<http://purl.org/dc/elements/1.1/#Title>",
            '"Example Title"'),
           ('<http://example.com/path/to/object>',
            '<http://purl.org/dc/elements/1.1/#Description>",
            '"This is an example description."'),
          ]
        """

class IRDFXML(Interface):
    """ Interface for a component that wants to generate RDF XML."""

    def xml():
        """ Return the RDF XML description of this component. """


class IRDAbout(Interface):
    """ Interface for a component that wants to generate RDF XML."""

    def about():
        """ Return the RDF XML description of this component. """

class IQuery(Interface):

    """ Any callable.  Returns a result set or None (no results) or
    throws an exception. """

    def __call__(store, *args):
        """ Eval a query with given args.  Returns a result Set.
        Queries throw QueryException to indicate failure."""


class IQueryChain(IQuery):

    """ Abstract class to combine a "chain" of queries into one result
    set.  QueryChains are themselves Queries, and can be nested. """


    def add(query):
        """ Append a query onto the chain """

    def getQueries():
        """ Return the chain of queries. """


class IQueryable(Interface):
    """ A generic catalog interface, there is nothing specificly in
    this interface about zemantic or semantic web notions, it provides
    for a query operation of any kind and could be used for other
    forms of catalogs like a port of textindexng.  ."""

    def query(query):
        """ Query the catalog with a query object, returning a sequence of results. """

class IZemanticEvent(Interface):
    """ When triples are added or removed from the storage, these
    events are fired.  Not sure if this interface is even necessary."""


class ITripleAfterAddEvent(Interface):
    """ When triples are added or removed from the storage, these
    events are fired.  Not sure if this interface is even necessary."""


class ITripleBeforeRemoveEvent(Interface):
    """ When triples are added or removed from the storage, these
    events are fired.  Not sure if this interface is even necessary."""


class ITripleStore(IQueryable):
    '''\
    Semantic Web Catalog.

    Zemantic "catalogs" (ie indexes) data expressed in the Resource
    Description Framework (RDF).  Any kind of content, whether inside Zope
    or from some outside source, can be cataloged if it can describe
    itself using the RDF standard.  Any kind of RDF vocabulary like RSS,
    OWL, DAML+OIL, Dublin Core, or any kind of XML schema or data can be
    expressed into the catalog.

    Once data is cataloged into Zemantic it can be queried using either
    the Python query interface or a TALES-based RDF query expression
    language.  Results of a query can be either a generator of result
    records or RDF in xml or NT format.

    Zemantic has two main components that are both configured as a local
    Zope 3 site utility.  The Zemantic utility is the actual catalog of
    meta-data and the Zontology utility is used to managed registered
    ontologies, or schemas, such as Dublin Core, FoaF
    (Friend-of-a-Friend), OWL, etc.

    In Semantic Web terms, Zemantic is a persistent triple store.  RDF
    is broken down into subject, predicate, and object relations
    (called triples) and each relation is indexed.  The triple store
    can then be queried for triples that match patterns.

    A Zemantic is queried by calling its query() method with a query
    object that provide zemantic.interfaces.IQuery.  See
    zemantic.query.Query for an example of such an object or the
    zemantic.expressions modules for example of query expressions.

    '''

    def notifyOn():
        """ Turn on triple add and remove notification. """

    def notifyOff():
        """ Turn off triple add and remove notification. """

    def clear():
        """ Clear the catalog.  Removes all relations. """

    def getStore():
        """ Return the catalog rdflib backend storage. """

    def parse(rdf, format="xml"):
        """ Parse RDF-XML into the catalog. """

    def add((subject, predicate, object)):
        """ Add one triple to the catalog.  """

    def remove((subject, predicate, object)):
        """ Remove one triple from the catalog. """

    def triples((subject, predicate, object), *args):
        """ Query the triple store. """

    def subjects(predicate=None, object=None):
        """ Return all subjects.  Optionally provide qualifying predicate and object. """

    def predicates(subject=None, object=None):
        """ Return all predicates. Optionally provide qualifying subject and object. """

    def objects(subject=None, predicate=None):
        """ Return all objects.  Optionally provide qualifying subject and predicate. """

    def subject_predicates(object=None):
        """ """

    def subject_objects(predicate=None):
        """ """

    def predicate_objects(subject=None):
        """ """

    def transitive_objects(subject, property, remember=None):
        """ """

    def transitive_subjects(predicate, object, remember=None):
        """ """

    def uniqueSubjects():
        """ All unique subjects. """

    def uniquePredicates():
        """ All unique predicates. """

    def uniqueObjects():
        """ All unique objects. """

    def rdfxml():
        """ Returns rdf xml representation of store. """

    def rdfnt():
        """ Returns rdf nt representation of store. """

    def __len__():
        """ Return the total number of triples in the store.  Might be
        expensive."""


class IContext(ITripleStore):

    def __str__():
        """ Returns context as string. """


class IInformationStore(IQueryable):
    """ An rdflib-style information store. """

    def notifyOn():
        """ Turn on triple add and remove notification. """

    def notifyOff():
        """ Turn off triple add and remove notification. """

    def clear():
        """ Clear the catalog.  Removes all relations. """

    def getStore():
        """ Return the catalog rdflib backend storage. """

    def parse(rdf, context, format="xml"):
        """ Parse RDF-XML into the catalog. """

    def add((subject, predicate, object), context):
        """ Add one triple to the catalog in a given context. """

    def remove((subject, predicate, object), context):
        """ Remove one triple from the catalog in a given context.   """

    def triples((subject, predicate, object), context, *args):
        """ Query the information store. """

    def getContext(context):
        """ Return a triple store of the given context. """

    def getContexts():
        """ Return a generator of all contexts in the information store. """

    def __len__():
        """ Return number of contexts in store. """

# we have to assert all of these interfaces here so that they work with Zope 3

from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal
from Products.CPSMailAccess.zemantic.rdflib.Identifier import Identifier

class IIdentifier(Interface):

    def n3():
        """ Return N3 representation of identifier. """

    def startswith(string):
        """ dummy. """

    def __cmp__(other):
        """ dummy. """

classImplements(Identifier, IIdentifier)
classImplements(URIRef, IIdentifier)
classImplements(BNode, IIdentifier)
classImplements(Literal, IIdentifier)

class IResult(Interface):
    subject = Attribute("Result subject.")
    predicate = Attribute("Result predicate.")
    object = Attribute("Result object.")

    def triple():
        """ """

class IResultSet(Interface):

    def rdfxml():
        """ Return rdfxml of result set. """

    def rdfnt():
        """ Return nt format of result set. """


