from Products.CPSMailAccess.zemantic.rdflib import RDF

from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.util import first, uniq, more_than

from Products.CPSMailAccess.zemantic.rdflib.syntax.serializer import AbstractSerializer
from Products.CPSMailAccess.zemantic.rdflib.syntax.serializers.XMLWriter import XMLWriter
from Products.CPSMailAccess.zemantic.rdflib.syntax.serializers.QNameProvider import QNameProvider, XMLLANG

class PrettyXMLSerializer(AbstractSerializer):

    short_name = "pretty-xml"

    def __init__(self, store):
        super(PrettyXMLSerializer, self).__init__(store)
        self.__serialized = {}

    def serialize(self, stream):
        self.__serialized = {}
        store = self.store

        qp = QNameProvider()
        self.writer = writer = XMLWriter(stream, qp)

        for namespace, prefix in store.ns_prefix_map.iteritems():
            qp.set_prefix(prefix, namespace)
        self.namespaceCount = len(store.ns_prefix_map)
        possible = uniq(store.predicates()) + uniq(store.objects(None, RDF.type))
        for predicate in possible:
            qp.compute(predicate)

        writer.push(RDF.RDF)
        writer.namespaces(qp.namespaces())

        # Write out subjects that can not be inline
        for subject in store.subjects():
            if (None, None, subject) in store:
                if (subject, None, subject) in store:
                    self.subject(subject, 1)
            else:
                self.subject(subject, 1)

        # write out anything that has not yet been reached
        for subject in store.subjects():
            self.subject(subject, 1)

        writer.pop(RDF.RDF)

        # Set to None so that the memory can get garbage collected.
        self.__serialized = None


    def subject(self, subject, depth=1):
        store = self.store
        writer = self.writer
        if not subject in self.__serialized:
            self.__serialized[subject] = 1
            type = first(store.objects(subject, RDF.type))
            element = type or RDF.Description
            writer.push(element)
            if isinstance(subject, BNode):
                if more_than(store.triples((None, None, subject)), 2):
                    writer.attribute(RDF.nodeID, subject)
            else:
                writer.attribute(RDF.about, subject)
            if (subject, None, None) in store:
                for predicate, object in store.predicate_objects(subject):
                    if not (predicate==RDF.type and object==type):
                        self.predicate(predicate, object, depth+1)
            writer.pop(element)

    def predicate(self, predicate, object, depth=1):
        writer = self.writer
        store = self.store
        writer.push(predicate)
        if isinstance(object, Literal):
            attributes = ""
            if object.language:
                writer.attribute(XMLLANG, object.language)
            if object.datatype:
                writer.attribute(RDF.datatype, object.datatype)
            writer.text(object)
        elif object in self.__serialized or not (object, None, None) in store:
            if isinstance(object, BNode):
                if more_than(store.triples((None, None, object)), 2):
                    writer.attribute(RDF.nodeID, object)
            else:
                writer.attribute(RDF.resource, object)
        else:
            if first(store.objects(object, RDF.first)): # may not have type RDF.List
                collection = object
                self.__serialized[object] = 1
                # TODO: warn that any assertions on object other than
                # RDF.first and RDF.rest are ignored... including RDF.List
                writer.attribute(RDF.parseType, "Collection")
                while collection:
                    item = first(store.objects(collection, RDF.first))
                    if item:
                        self.subject(item)
                    collection = first(store.objects(collection, RDF.rest))
                    self.__serialized[collection] = 1
            else:
                self.subject(object, depth+1)
        writer.pop(predicate)
