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
<Work rdf:about="http://zemantic.org/zemantic/utils.py"
  dc:title="zemantic.utils"
  dc:date="2005"
  dc:description="Misc stuff.">
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

from lib.ZODBBackend import ZODBBackend
from interfaces import ITripleStore
from zope.interface import implements
from urllib import quote, quote_plus

from rdflib.Literal import Literal
from rdflib.BNode import BNode
from rdflib.URIRef import URIRef

from triplestore import TripleStore
from query import Query

class TripleStoreToDotAdapter(object):

    def __init__(self, cat, title=''):
        """
        Turn zemantic into a DOT graph

        """
        self.cat = cat
        self.title = title

    def toDot(self):
        out = []
        bcount = 0
        lcount = 0
        out.append('digraph "%s" {' % self.title)
#        out.append('node [fontname="Courier",fontsize=10,color=Black,fontcolor=Blue];')
#        out.append('edge [fontname="Courier",fontsize=10,color=Darkgreen,fontcolor=Red];')
        out.append('rankdir=LR;')
        cat = self.cat
        for r in cat.query(Query()):

            sname = oname = None
            if r.subject.startswith('_'):
                bcount += 1
                sname = 'Blank_' + str(bcount)
            else:
                sname = r.subject.n3()

            if r.object.startswith('"'):
                lcount += 1
                oname = 'Literal_' + str(lcount)
            else:
                oname = r.object.n3()

            out.append('%s [label="%s"];' % (sname.replace('"', ''), r.subject.n3().replace('"', '\"')))
            out.append('%s -> %s [label="%s"];' % (sname.replace('"', ''), oname.replace('"', ''), r.predicate.n3().replace('"', '\"')))
            out.append('%s [shape="box", label="%s"];' % (oname.replace('"', ''), r.object.n3().replace('"', '\"')))

        out.append('}')
        return '\n'.join(out)


def shorten(s):
    if s > 30:
        return s[:13]+'...'+s[-13:]
    return s


