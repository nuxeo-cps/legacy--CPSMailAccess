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
<Work rdf:about="http://zemantic.org/zemantic/result.py"
  dc:title="zemantic.result"
  dc:date="2005"
  dc:description="Result objects.">
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


from interfaces import IResult, IResultSet
from zope.interface import implements
from zope.security.proxy import removeSecurityProxy

from BTrees.OOBTree import OOSet
from rdflib.TripleStore import TripleStore
from rdflib.backends.InMemoryBackend import InMemoryBackend

class Result(object):

    implements(IResult)

    def __init__(self, (subject, predicate, object)):
        self.subject = subject
        self.predicate = predicate
        self.object = object

    def triple(self):
        return self.subject, self.predicate, self.object

    def __str__(self):
        return "<%s, %s, %s>" % (`self.subject`, `self.predicate`, `self.object`)

class ResultSet(object):

    implements(IResultSet)

    def __init__(self, data):
        self.data = TripleStore(backend=InMemoryBackend())
        for result in data:
            if result is not None:
                s, p, o = result.triple()
                s = removeSecurityProxy(s)
                p = removeSecurityProxy(p)
                o = removeSecurityProxy(o)
                self.data.add((s, p, o))

    def rdfxml(self):
        return self.data.serialize()

    def rdfnt(self):
        return self.data.serialize("nt") 
