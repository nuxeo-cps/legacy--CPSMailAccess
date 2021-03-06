# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziad� <tz@nuxeo.com>
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
#
"""
  mailsearch holds all mail searches
"""
import os
import sre_constants
from encodings import exceptions as encoding_exceptions

from Globals import InitializeClass

from zope.interface import implements
from BTrees.OOBTree import OOBTree

from utils import parseDateString, removeHTML, decodeHeader, parseRefs
from interfaces import IMailCatalog, IMailFolder

from zemantic.triplestore import TripleStore
from zemantic.interfaces import IRDFThreeTuples
from zemantic.public import Any
from zemantic.query import Query

from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal
from Products.CPSMailAccess.normalizer import getNormalizer

def _unify(elements):

    def __unify(item):
        if not type(item) in (str, URIRef):
            return item.triple()[0]
        else:
            return item

    elements[:] = map(__unify, elements)

def intersection(x, y):
    """ intersect triples, strings,unicode and URIRef """
    _unify(x)
    _unify(y)
    result = []

    for item in x:
        if item in y and item not in result:
            result.append(item)

    return result

def union(x, y=[]):
    """ unions triples, strings, unicode and URIRef """
    _unify(x)
    result = []

    if y != []:
        _unify(y)
        both = x + y
    else:
        both = x

    for item in both:
        if item not in result:
            result.append(item)

    return result

def unifyList(list_):
    """ returns unified list """
    _unify(list_)
    return list_

def get_uri(portal_object):
    return URIRef(unicode(portal_object.absolute_url())) # zope 2 dependant

# normalizer
normalizer = getNormalizer()

class ZemanticMessageAdapter:

    implements(IRDFThreeTuples)

    default_charset = 'ISO-8859-15'
    headers = (u'message-id', u'date', u'from', u'to', u'subject', u'cc',
               u'sender')
    message_relation = ((u'references', u'thread'),
                        (u'in-reply-to', u'replies'))

    def __init__(self, message, catalog, full_indexation=False):
        self.context = message
        self.catalog = catalog
        self.full_indexation = full_indexation
        charset = message.getHeader('Charset')
        if charset is None or charset == []:
            self.charset = self.default_charset
        else:
            self.charset = charset[0]

    def _headerToUnicode(self, value):
        if isinstance(value, str):
            try:
                value = value.decode(self.charset)
            except (encoding_exceptions.LookupError,
                    UnicodeDecodeError):
                value = value.decode(self.default_charset)
        return value

    def _normalize(self, word):
        return normalizer.normalize(word)

    def threeTuples(self, index_relations=True):
        """ give zemantic the sequence of relations """
        message = self.context

        if message.absolute_url() == '':
            return []

        ob_uri = get_uri(message)

        triples = []
        if self.full_indexation:
            headers = message.getHeaders()
        else:
            headers = self.headers

        for header in headers:
            header_name = header
            header_name = self._headerToUnicode(header_name)
            try:
                values = message.getHeader(header_name)
            except UnicodeDecodeError:
                values = []
            for value in values:
                header_name = header_name.lower()
                relation = URIRef(header_name)
                value = decodeHeader(value)
                value = self._headerToUnicode(value)
                value = self._normalize(value)
                if header_name == 'date':
                    # fixed string date indexing
                    cdate = parseDateString(value)
                    value = unicode(cdate.strftime('%d/%m/%Y'))
                    value = URIRef(value)
                else:
                    if len(value) > 0 and value[0] in u'?*':
                        value = u'_' + value
                    value = Literal(value)

                triple = (ob_uri, relation, value)
                triples.append(triple)

        # a triple for the direct body
        if self.full_indexation:
            body = message.getDirectBody()
            if body is not None:
                body = removeHTML(body)

            body = self._headerToUnicode(body)
            body = self._normalize(body)
            body = Literal(body)
            triples.append((ob_uri, URIRef(u'body'), body))

        # a triple for folder
        folder = message.getMailFolder()
        if folder is None or not IMailFolder.providedBy(folder):
            folder_name = URIRef(u'_#_orphan_#_')
        else:
            folder_name = URIRef(unicode(folder.server_name))

        triples.append((ob_uri, URIRef(u'folder'), folder_name))

        # relations with other mails
        if index_relations:
            uris = []
            for relation in self.message_relation:
                # all relations are based on message ids
                relation_name = relation[0]
                relation_object = relation[1]
                try:
                    values = message.getHeader(relation_name)
                except UnicodeDecodeError:
                    values = []
                for value in values:
                    # let's try to find the message id in _message_ids
                    value = decodeHeader(value)
                    value = self._headerToUnicode(value)
                    refs = parseRefs(value)

                    for ref in refs:
                        if not self.catalog._message_ids.has_key(ref):
                            continue
                        uri = self.catalog._message_ids[ref]
                        if uri in uris:
                            continue
                        relation_object = unicode(relation_object)
                        relation_ref = URIRef(relation_object)
                        relation = (ob_uri, relation_ref, uri)
                        triples.append(relation)
                        # making the backed relation
                        back_relation_ref = URIRef(u'back-'+relation_object)
                        back_relation = (uri, back_relation_ref, ob_uri)
                        triples.append(back_relation)
                        uris.append(uri)
        return triples

class ZemanticMailCatalog(TripleStore):

    implements(IMailCatalog)

    def __init__(self, backend=None):
        TripleStore.__init__(self, backend)
        self._message_ids = OOBTree()

    def clear(self):
        TripleStore.clear(self)
        self._message_ids = OOBTree()

    def _headerToUnicode(self, value):
        if isinstance(value, str):
            try:
                value = value.decode('ISO-8859-15')
            except (encoding_exceptions.LookupError,
                    UnicodeDecodeError):
                value = value.decode(self.default_charset)
        return value

    def indexMessage(self, message, full_indexation=False,
                     index_relations=True):
        """ index message """
        zmessage = ZemanticMessageAdapter(message, self, full_indexation)
        tuples = zmessage.threeTuples(index_relations)

        # adding message to _message_ids
        ob_uri = get_uri(message)
        message_id = message.getHeader('message-id')
        if message_id is not None and message_id != []:
            message_id = self._headerToUnicode(message_id[0])
            self._message_ids[message_id] = ob_uri
        self.addTriples(tuples)

    def unIndexMessage(self, message):
        """ unindex message """
        # undindexing is removing all triples where message is the subject
        zmessage = ZemanticMessageAdapter(message, self, False)
        # adding message to _message_ids
        message_id = message.getHeader('message-id')
        if message_id is not None and message_id != []:
            if self._message_ids.has_key(message_id):
                del self._message_ids[message_id]
        tuples = zmessage.threeTuples()
        for tuple_ in tuples:
            try:
                self.remove(tuple_)
            except (ZeroDivisionError, KeyError, sre_constants.error):
                pass

    def make_query(self, query_tuple):
        """ creates a query object and query """
        subject = query_tuple[0]
        object = u'<%s>' % query_tuple[1]
        if query_tuple[2] is None:
            predicate = Any
        else:
            predicate = query_tuple[2]
        q = Query(subject, object, predicate)
        return self.query(q)

InitializeClass(ZemanticMailCatalog)
