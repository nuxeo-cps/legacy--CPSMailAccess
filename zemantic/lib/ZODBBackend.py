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

Any = None

class ZODBBackend(Persistent):
    """\
    A ZODB implementation of a triple store backend.

    Uses nested BTrees to store triples. Each triple is stored in
    three such indices as follows spo[s][p][o] = 1 and pos[p][o][s] =
    1 and osp[o][s][p] = 1.

    This is basicly an adaptation of rdflib's InMemoryBackend using
    BTrees instead of dictionaries.  This is not storage optimal!  For
    a size optimized version see IOZODBBackend.py
    """    

    def __init__(self):
        
        # indexed by [subject][predicate][object] = 1
        self.spo = OOBTree()

        # indexed by [predicate][object][subject] = 1
        self.pos = OOBTree()

        # indexed by [object][subject][predicate] = 1
        self.osp = OOBTree()

    def uniqueSubjects(self):
        return self.spo.keys()

    def uniquePredicates(self):
        return self.pos.keys()

    def uniqueObjects(self):
        return self.osp.keys()

    def add(self, (subject, predicate, object)):
        """\
        Add a triple to the store.
        """
        # add dictionary entries for spo[s][p][p] = 1, pos[p][o][s] =
        # 1, and osp[o][s][p] = 1, creating the nested dictionaries
        # where they do not yet exits.
        
        spo = self.spo
        if spo.has_key(subject):
            po = spo[subject]
        else:
            po = spo[subject] = OOBTree()
        if po.has_key(predicate):
            o = po[predicate]
        else:
            o = po[predicate] = OOBTree()
        o[object] = 1

        pos = self.pos
        if pos.has_key(predicate):
            os = pos[predicate]
        else:
            os = pos[predicate] = OOBTree()
        if os.has_key(object):
            s = os[object]
        else:
            s = os[object] = OOBTree()
        s[subject] = 1

        osp = self.osp
        if osp.has_key(object):
            sp = osp[object]
        else:
            sp = osp[object] = OOBTree()
        if sp.has_key(subject):
            p = sp[subject]
        else:
            p = sp[subject] = OOBTree()
        p[predicate] = 1

    def remove(self, (subject, predicate, object)):
        for subject, predicate, object in self.triples((subject, predicate, object)):
            del self.spo[subject][predicate][object]
            del self.pos[predicate][object][subject]
            del self.osp[object][subject][predicate]

    def triples(self, (subject, predicate, object)):
        """A generator over all the triples matching """
        if subject!= Any: # subject is given
            spo = self.spo
            if spo.has_key(subject):
                subjectDictionary = spo[subject]
                if predicate != Any: # subject+predicate is given
                    if subjectDictionary.has_key(predicate):
                        if object!= Any: # subject+predicate+object is given
                            if subjectDictionary[predicate].has_key(object):
                                yield subject, predicate, object
                            else: # given object not found
                                pass
                        else: # subject+predicate is given, object unbound
                            for o in subjectDictionary[predicate].keys():
                                yield subject, predicate, o
                    else: # given predicate not found
                        pass
                else: # subject given, predicate unbound
                    for p in subjectDictionary.keys():
                        if object != Any: # object is given
                            if subjectDictionary[p].has_key(object):
                                yield subject, p, object
                            else: # given object not found
                                pass
                        else: # object unbound
                            for o in subjectDictionary[p].keys():
                                yield subject, p, o
            else: # given subject not found
                pass
        elif predicate != Any: # predicate is given, subject unbound
            pos = self.pos
            if pos.has_key(predicate):
                predicateDictionary = pos[predicate]
                if object != Any: # predicate+object is given, subject unbound
                    if predicateDictionary.has_key(object):
                        for s in predicateDictionary[object].keys():
                            yield s, predicate, object
                    else: # given object not found
                        pass
                else: # predicate is given, object+subject unbound
                    for o in predicateDictionary.keys():
                        for s in predicateDictionary[o].keys():
                            yield s, predicate, o
        elif object != Any: # object is given, subject+predicate unbound
            osp = self.osp
            if osp.has_key(object):
                objectDictionary = osp[object]
                for s in objectDictionary.keys():
                    for p in objectDictionary[s].keys():
                        yield s, p, object
        else: # subject+predicate+object unbound
            spo = self.spo
            for s in spo.keys():
                subjectDictionary = spo[s]
                for p in subjectDictionary.keys():
                    for o in subjectDictionary[p].keys():
                        yield s, p, o

    def __len__(self):
        #@@ optimize
        i = 0
        for triple in self.triples((None, None, None)):
            i += 1
        return i
        
