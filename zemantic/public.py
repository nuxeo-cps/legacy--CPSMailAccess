
Any = None

from interfaces import *

from rdflib.URIRef import URIRef
from rdflib.BNode import BNode
from rdflib.Literal import Literal
from rdflib.Identifier import Identifier

from triplestore import TripleStore
from informationstore import InformationStore
from query import Query
from result import Result, ResultSet

from expressions import eval
