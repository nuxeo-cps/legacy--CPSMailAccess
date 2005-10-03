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
<Work rdf:about="http://zemantic.org/zemantic/expressions.py"
  dc:title="zemantic.expressions"
  dc:date="2005"
  dc:description="TALES Zemantic expressions.">
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

from zope.app import zapi
from types import UnicodeType, TupleType
from zope.interface import implements
from zope.security.proxy import removeSecurityProxy
from zope.tales.tales import _valid_name, _parse_expr, NAME_RE, Undefined, CompilerError
from zope.tales.interfaces import ITALESExpression, ITALESFunctionNamespace

from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal
from Products.CPSMailAccess.zemantic.rdflib.Identifier import Identifier

from interfaces import *
from query import Query, UnionChain
from result import ResultSet

import sys
from zope.tales.engine import Engine
from zope.tales.tales import Context

class ZemanticExpr(object):
    """\
Zemantic query expressions.

  A zemantic expression has the triple expression form:

    (<s expr>, <p expr>, <o expr>)

  The results of each sub expression in the triple pattern are used to
  query the nearest zemantic catalog site utility.

  Sub-expressions can be any kind of TALES expression (string, nocall,
  not, path, python etc.) but the expression must return one of the
  following:

     None - Matches all ident

     string or unicode - a string or unicode identifier in N3 format.

     IIdentifier implementor (BNode, URIRef, Literal) - an identifier
     object.

  Inner queries can be defined by returning:

     3-tuple - defines standard inner query.

     IQuery implementor - defines custom inner query.

  The actual query logic is not implemented by the expression, for
  that look at zemantic.query.Query.

    """

    implements(ITALESExpression)

    def __init__(self, name, expr, engine):
        self._s = expr
        self._name = name
        self.engine = engine
        self.expr = self._compile(expr)

    def _compile(self, expression):
        m = _parse_expr(expression)
        if m:
            type = m.group(1)
            expr = expression[m.end():]
        else:
            type = "python"
            expr = expression
        try:
            handler = self.engine.getTypes()[type]
        except KeyError:
            raise CompilerError, ('Unrecognized expression type "%s".' % type)
        return handler(type, expr, self.engine)


    def __call__(self, econtext):

        c = zapi.queryUtility(ITripleStore)
        o = zapi.queryUtility(IInformationStore)

        # eval each expression, stuffing the result in a Query object.
        # Query will raise an error if the argument is not proper
        # like.

        if c is not None:
            econtext.setLocal('zem', c)
        if o is not None:
            econtext.setLocal('zon', o)

        econtext.setLocal('Any', None)
        econtext.setLocal('URIRef', URIRef)
        econtext.setLocal('BNode', BNode)
        econtext.setLocal('Literal', Literal)

        q = self.expr(econtext)

        if type(q) is TupleType:
            if len(q) != 3:
                raise ValueError, "Zemantic expression must be a " \
                                  "3 element tuple or provide IQuery"
            s, p, o = q
            q = Query(removeSecurityProxy(s),
                      removeSecurityProxy(p),
                      removeSecurityProxy(o))

        elif not IQuery.providedBy(q):
            raise ValueError, "Zemantic expression must be a " \
                              "3 element tuple or provide IQuery"
        else:
            q = removeSecurityProxy(q)

        for result in c.query(q):
            yield result

    def __str__(self):
        return self._s

    def __repr__(self):
        return '<ZemanticExpr %s>' % self._s


class RDFExpr(object):
    """\
    Render results of a Zemantic expression into RDF XML.

    """

    implements(ITALESExpression)

    def __init__(self, name, expr, engine):
        self._s = expr
        self._name = name
        self.engine = engine
        self.expr = self._compile(expr)

    def _compile(self, expression):
        m = _parse_expr(expression)
        if m:
            type = m.group(1)
            expr = expression[m.end():]
        else:
            type = "zemantic"
            expr = expression
        try:
            handler = self.engine.getTypes()[type]
        except KeyError:
            raise CompilerError, ('Unrecognized expression type "%s".' % type)
        return handler(type, expr, self.engine)


    def __call__(self, econtext):

        c = zapi.queryUtility(ITripleStore)
        o = zapi.queryUtility(IInformationStore)

        if c is not None:
            econtext.setLocal('zem', c)
        if o is not None:
            econtext.setLocal('zon', o)


        econtext.setLocal('Any', None)
        econtext.setLocal('URIRef', URIRef)
        econtext.setLocal('BNode', BNode)
        econtext.setLocal('Literal', Literal)

        # eval each expression, stuffing the result in a Query object.
        # Query will raise an error if the argument is not proper
        # like.

        return ResultSet(self.expr(econtext)).rdfxml()

    def __str__(self):
        return self._s

    def __repr__(self):
        return '<RDFExpr %s>' % self._s

def eval(expr, context=None):

    c = zapi.queryUtility(ITripleStore, context=context)
    o = zapi.queryUtility(IInformationStore, context=context)

    econtext = Context(Engine, {})

    if c is not None:
        econtext.setLocal('zem', c)
    if o is not None:
        econtext.setLocal('zon', o)

    econtext.setLocal('Any', None)
    econtext.setLocal('URIRef', URIRef)
    econtext.setLocal('BNode', BNode)
    econtext.setLocal('Literal', Literal)

    bytecode = Engine.compile(expr)
    return bytecode(econtext)
