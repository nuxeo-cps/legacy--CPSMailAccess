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

from persistent import Persistent
from BTrees.OOBTree import OOBTree

from ZODBBackend import ZODBBackend

ANY = None

class ZODBContextBackend(Persistent):
    """
    Experimental persistent InformationStore backend.  Basicly four
    dimensions storing"context" information also.  Not currently used.

    """    
    def __init__(self):

        self.contexts = OOBTree()
        
    def uniqueSubjects(self):
        for ts in self.contexts.values():
            yield ts.spo.keys()

    def uniquePredicates(self):
        for ts in self.contexts.values():
            yield ts.spo.keys()

    def uniqueObjects(self):
        for ts in self.contexts.values():
            yield ts.spo.keys()

    def add(self, (subject, predicate, object), context=None):
        self.contexts[context].add((subject, predicate, object))
        

    def remove(self, (subject, predicate, object), context=None):
        self.contexts[context].remove((subject, predicate, object))        

    def triples(self, (subject, predicate, object), context=None):
        yield self.contexts[context].triples((subject, predicate, object))        

    def __len__(self):
        #@@ optimize
        i = 0
        for triple in self.triples((None, None, None)):
            i += 1
        return i
        
