
Any = None

from interfaces import *

from Products.CPSMailAccess.zemantic.rdflib.URIRef import URIRef
from Products.CPSMailAccess.zemantic.rdflib.BNode import BNode
from Products.CPSMailAccess.zemantic.rdflib.Literal import Literal
from Products.CPSMailAccess.zemantic.rdflib.Identifier import Identifier

from triplestore import TripleStore
from informationstore import InformationStore
from query import Query
from result import Result, ResultSet

from expressions import eval
