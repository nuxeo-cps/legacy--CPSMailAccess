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
<Work rdf:about="http://zemantic.org/zemantic/zemantic.py"
  dc:title="zemantic.events"
  dc:date="2005"
  dc:description="Catalog events and default handling.">
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

from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal
from Products.CPSMailAccess.zemantic.rdflib.Identifier import Identifier

from query import Query
from interfaces import IZemanticEvent, ITripleAfterAddEvent, ITripleBeforeRemoveEvent

from zope.interface import implements
from zope.interface.verify import verifyClass

from zope.event import notify

class ZemanticEvent(object):
    """
    A zemantic event.  Instanciated by zemantic catalogs when the
    store is manipluated.
    """

    implements(IZemanticEvent)

    def __init__(self, data=()):
        self.data = data


class TripleAfterAddEvent(ZemanticEvent):

    implements(ITripleAfterAddEvent)


class TripleBeforeRemoveEvent(ZemanticEvent):

    implements(ITripleBeforeRemoveEvent)


def afterAdd(data):
    notify(TripleAfterAddEvent(data))


def beforeRemove(data):
    notify(TripleBeforeRemoveEvent(data))
