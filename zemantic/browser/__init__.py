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
<Work rdf:about="http://zemantic.org/zemantic/browser.py"
  dc:title="zemantic.browser"
  dc:date="2005"
  dc:description="Browser views for z3.">
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

Any = None

from zope.i18nmessageid import MessageIDFactory
from zope.app import zapi
from zope.security.proxy import removeSecurityProxy

from rdflib.URIRef import URIRef
from rdflib.BNode import BNode
from rdflib.Literal import Literal
from rdflib.Identifier import Identifier
from rdflib.exceptions import ParserError

from zemantic.utils import TripleStoreToDotAdapter
from zemantic.query import Query
import popen2
import urllib, os, time
from xml import sax
from tempfile import NamedTemporaryFile
from StringIO import StringIO

from zemantic.triplestore import TripleStore
from zemantic.resources import FileResource, DirectoryResource
from zemantic.result import ResultSet

_ = MessageIDFactory('zemantic')

class TripleStoreView:

    def shorty(self, s):
        """ dumb ui method """
        if len(s) > 30:
            return s[:15]+'...'+s[-15:]
        return s    

    def n3(self, obj):
        return obj.n3()

    def uniquePredicatesView(self):
        r = []
        for i in self.context.uniquePredicates():
            r.append(i)
        return r

    def clear(self):
        self.context.clear()

    def query(self, subject, predicate, object):
        q = Query(subject, predicate, object)
            
        return self.context.query(q)

    def queryRDF(self, subject, predicate, object):
        if subject in ('Any', 'None'):
            subject = Any
        if predicate in ('Any', 'None'):
            predicate = Any
        if object in ('Any', 'None'):
            object = Any
        q = Query(subject, predicate, object)
        self.request.response.setHeader('content-type', 'text/xml')
        return ResultSet(self.context.query(q)).rdfxml()

    def quote(self, str):
        return urllib.quote(str)

    def genSVG(self):
        x = TripleStoreToDotAdapter(self.context, "RDF Graph")
        d = x.toDot()
        i = NamedTemporaryFile()
        i.write(d)
        i.flush()
        self.request.response.setHeader('content-type', 'image/svg+xml')
        return getoutput('dot -Tsvg %s' % i.name)
        
    def genJPG(self):
        x = TripleStoreToDotAdapter(self.context, "RDF Graph")
        d = x.toDot()
        i = NamedTemporaryFile()
        o = NamedTemporaryFile()
        i.write(d)
        i.flush()
        getoutput('dot -Tjpg %s -o %s' % (i.name, o.name))
        f = open(o.name)
        self.request.response.setHeader('content-type', 'image/jpg')
        return f.read()

    def genDOT(self):
        x = TripleStoreToDotAdapter(self.context, "RDF Graph")
        return x.toDot()

    def addURL(self):
        url = self.request.form['add_url']
        f = urllib.urlopen(url)
        self.context.parse(f)
        self.request.response.redirect('zemantic.html')

    def clear(self):
        self.context.clear()
        self.request.response.redirect('zemantic.html')

class InformationStoreView:

    def loadstuff(self):
        print 'getting directory'
        dircon = 'http://www.schemaweb.info/DirectoryMeta.aspx'
        directory = urllib.urlopen(dircon)
        print 'got directory'
        dircon =  URIRef(dircon)
        self.context.parse(directory, dircon)
        n = 0
        q = Query(Any, u'<http://www.schemaweb.info/schemas/meta/rdf/rdf-meta>', Any, dircon)
        for result in self.context.query(q):
            if result is not None:
                time.sleep(1)
                try:
                    print 'fetching %s' % result.object
                    f = urllib.urlopen(removeSecurityProxy(result.object))
                    y = TripleStore()
                    y.parse(f)
                    q = Query(Any, u'<http://www.schemaweb.info/schemas/meta/rdf/namespace>', Any)
                    for result2 in y.query(q):

                        u2 = 'http://www.schemaweb.info/webservices/rest/GetRDF.aspx?namespace=%s' % urllib.quote_plus(removeSecurityProxy(result2.object))
                        print 'fetching %s' % u2
                        f = urllib.urlopen(removeSecurityProxy(u2))
                        print 'parsing'
                        self.context.parse(f, URIRef(removeSecurityProxy(result2.object)))
                        get_transaction().commit()
                except (LookupError, sax.SAXParseException, ParserError):
                    print "Can't load %s" % result.object

        self.request.response.redirect('contents.html')

    def getClassNames(self):
        for name, child in self.context.items():
            for klass in self.child.classes.keys():
                yield klass

    def getPropertyNames(self):
        for name, child in self.context.items():
            for prop in self.child.properties.keys():
                yield prop

    def getClassLen(self):
        return 0 # too expensive
        s = 0
        for name, child in self.context.items():
            s += len(child.classes)
        return s

    def getPropertyLen(self):
        return 0 # too expensive
        s = 0
        for name, child in self.context.items():
            s += len(child.properties)
        return s

    def getUniqueSubjectLen(self):
        s = 0
        for name, child in self.context.items():
            s += len(list(child.uniqueSubjects()))
        return s

    def getUniquePredicateLen(self):
        s = 0
        for name, child in self.context.items():
            s += len(list(child.uniquePredicates()))
        return s

    def getUniqueObjectLen(self):
        s = 0
        for name, child in self.context.items():
            s += len(list(child.uniqueObjects()))
        return s

    def getTotalTriples(self):
        s = 0
        for context in self.context.getContexts():
            s += len(context)
        return s

    def getTotalContexts(self):
        return len(self.context)


from zope.app.container.browser.contents import Contents
    

# Get the output from a shell command into a string.
# The exit status is ignored; a trailing newline is stripped.
# Assume the command will work with '{ ... ; } 2>&1' around it..
#
def getoutput(cmd):
    """Return output (stdout or stderr) of executing cmd in a shell."""
    return getstatusoutput(cmd)[1]


# Ditto but preserving the exit status.
# Returns a pair (sts, output)
#
def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell."""
    import os
    sout = os.popen(cmd, 'r')
    text = sout.read()
    sts = sout.close()
    if sts is None: sts = 0
    if text[-1:] == '\n': text = text[:-1]
    return sts, text
