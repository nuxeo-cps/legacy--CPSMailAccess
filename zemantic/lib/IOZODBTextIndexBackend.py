##############################################################################
#
# Copyright (c) 2004-1005 Michel Pelletier and Contributors
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
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree

Any = None

from zemantic.index.text.okapiindex import OkapiIndex as TextIndex
from zemantic.index.text.lexicon import Lexicon
from zemantic.index.text.lexicon import Splitter, CaseNormalizer, StopWordRemover

from rdflib.Literal import Literal

class IOZODBTextIndexBackend(Persistent):
    """\
    An integer-key optimized ZODB implementation of a triple store
    backend.

    Experimentally text indexes literal string values.

    Uses nested BTrees to store triples. Each triple is stored in
    three such indices as follows spo[s][p][o] = 1 and pos[p][o][s] =
    1 and osp[o][s][p] = 1.

    Unlike ZODBBackend, uses integer keys and IOBTrees for more
    efficient data storage.  Maintains a forward/reverse index of
    integers keys to identifiers, thus storing the variable-sized
    identifier only once and alway referring to it with a fixed size
    integer.  Storage is typically half that of ZODBBackend or better,
    especially for large identifiers or literals.

    """

    def __init__(self):

        # indexed by [subject][predicate][object] = 1
        self.spo = IOBTree()

        # indexed by [predicate][object][subject] = 1
        self.pos = IOBTree()

        # indexed by [object][subject][predicate] = 1
        self.osp = IOBTree()

        # indexes integer keys to identifiers
        self.forward = IOBTree()

        # reverse index of forward
        self.reverse = OIBTree()

        # a text index lexicon
        self.lexicon = Lexicon(Splitter(), CaseNormalizer(), StopWordRemover())

        # text index for literal strings
        self.texti = TextIndex(self.lexicon)

        self.count = 0

    def intToIdentifier(self, (si, pi, oi)):
        """ Resolve an integer triple into identifers. """
        return (self.forward[si], self.forward[pi], self.forward[oi])

    def identifierToInt(self, (s, p, o)):
        """ Resolve an identifier triple into integers. """
        return (self.reverse[s], self.reverse[p], self.reverse[o])

    def uniqueSubjects(self):
        for si in self.spo.keys():
            yield self.forward[si]

    def uniquePredicates(self):
        for pi in self.pos.keys():
            yield self.forward[pi]

    def uniqueObjects(self):
        for oi in self.osp.keys():
            yield self.forward[oi]

    def add(self, (subject, predicate, object)):
        """\
        Add a triple to the store.
        """

        f = self.forward
        r = self.reverse

        # assign keys for new identifiers

        if not r.has_key(subject):
            si=randid()
            while not f.insert(si, subject):
                si=randid()
            r[subject] = si
        else:
            si = r[subject]

        if not r.has_key(predicate):
            pi=randid()
            while not f.insert(pi, predicate):
                pi=randid()
            r[predicate] = pi
        else:
            pi = r[predicate]

        if not r.has_key(object):
            oi=randid()
            while not f.insert(oi, object):
                oi=randid()
            r[object] = oi
        else:
            oi = r[object]

        # if it's a literal, text index it
        if isinstance(object, Literal):
            self.texti.index_doc(oi, object)

        # add dictionary entries for spo[s][p][p] = 1, pos[p][o][s] =
        # 1, and osp[o][s][p] = 1, creating the nested IOBTree
        # where they do not yet exits.

        spo = self.spo
        if spo.has_key(si):
            po = spo[si]
        else:
            po = spo[si] = IOBTree()
        if po.has_key(pi):
            o = po[pi]
        else:
            o = po[pi] = IOBTree()
        o[oi] = 1

        pos = self.pos
        if pos.has_key(pi):
            os = pos[pi]
        else:
            os = pos[pi] = IOBTree()
        if os.has_key(oi):
            s = os[oi]
        else:
            s = os[oi] = IOBTree()
        s[si] = 1

        osp = self.osp
        if osp.has_key(oi):
            sp = osp[oi]
        else:
            sp = osp[oi] = IOBTree()
        if sp.has_key(si):
            p = sp[si]
        else:
            p = sp[si] = IOBTree()
        p[pi] = 1

        self.count = self.count + 1

    def remove(self, (subject, predicate, object)):
        for subject, predicate, object in self.triples((subject, predicate, object)):
            si, pi, oi = self.identifierToInt((subject, predicate, object))
            f = self.forward
            r = self.reverse
            del self.spo[si][pi][oi]
            del self.pos[pi][oi][si]
            del self.osp[oi][si][pi]

            self.count = self.count - 1

            # grr!! hafta ref-count these before you can collect them dumbass!
#             del f[si]
#             del f[pi]
#             del f[oi]
#             del r[subject]
#             del r[predicate]
#             del r[object]

# don't forget to clean up the text index too!

    def triples(self, (subject, predicate, object)):
        """A generator over all the triples matching """
        si = pi = oi = ois = Any
        if subject is not Any:
            si = self.reverse[subject]
        if predicate is not Any:
            pi = self.reverse[predicate]
        if object is not Any:
            if isinstance(object, Literal):
                ois = self.texti.search_glob(object)

                if len(ois) == 0:
                    try:
                        ois = self.texti.search_phrase(object)
                    except ZeroDivisionError:
                        ois = []

                if len(ois) == 0:
                    oi = self.reverse[object]
                    ois = Any
            else:
                oi = self.reverse[object]

        if si!= Any: # subject is given
            spo = self.spo
            if spo.has_key(si):
                subjectDictionary = spo[si]
                if pi != Any: # subject+predicate is given
                    if subjectDictionary.has_key(pi):
                        if oi != Any: # subject+predicate+object is given
                            if subjectDictionary[pi].has_key(oi):
                                yield self.intToIdentifier((si, pi, oi))
                            else: # given object not found
                                pass
                        elif ois != Any:
                            for oi in ois.keys():
                                if subjectDictionary[pi].has_key(oi):
                                    yield self.intToIdentifier((si, pi, oi))
                                else: # given object not found
                                    pass
                        else: # subject+predicate is given, object unbound
                            for o in subjectDictionary[pi].keys():
                                yield self.intToIdentifier((si, pi, o))
                    else: # given predicate not found
                        pass
                else: # subject given, predicate unbound
                    for p in subjectDictionary.keys():
                        if oi != Any: # object is given
                            if subjectDictionary[p].has_key(oi):
                                yield self.intToIdentifier((si, p, oi))
                            else: # given object not found
                                pass
                        elif ois != Any:
                            for oi in ois.keys():
                                if subjectDictionary[p].has_key(oi):
                                    yield self.intToIdentifier((si, p, oi))
                                else: # given object not found
                                    pass
                        else: # object unbound
                            for o in subjectDictionary[p].keys():
                                yield self.intToIdentifier((si, p, o))
            else: # given subject not found
                pass
        elif pi != Any: # predicate is given, subject unbound
            pos = self.pos
            if pos.has_key(pi):
                predicateDictionary = pos[pi]
                if oi != Any: # predicate+object is given, subject unbound
                    if predicateDictionary.has_key(oi):
                        for s in predicateDictionary[oi].keys():
                            yield self.intToIdentifier((s, pi, oi))
                    else: # given object not found
                        pass
                elif ois != Any:
                    for oi in ois.keys():
                        if predicateDictionary.has_key(oi):
                            for s in predicateDictionary[oi].keys():
                                yield self.intToIdentifier((s, pi, oi))
                        else: # given object not found
                            pass
                else: # predicate is given, object+subject unbound
                    for o in predicateDictionary.keys():
                        for s in predicateDictionary[o].keys():
                            yield self.intToIdentifier((s, pi, o))
        elif oi != Any: # object is given, subject+predicate unbound
            osp = self.osp
            if osp.has_key(oi):
                objectDictionary = osp[oi]
                for s in objectDictionary.keys():
                    for p in objectDictionary[s].keys():
                        yield self.intToIdentifier((s, p, oi))
        elif ois != Any: # object text search on literals
            for oi in ois.keys():
                osp = self.osp
                if osp.has_key(oi):
                    objectDictionary = osp[oi]
                    for s in objectDictionary.keys():
                        for p in objectDictionary[s].keys():
                            yield self.intToIdentifier((s, p, oi))

        else: # subject+predicate+object unbound
            spo = self.spo
            for s in spo.keys():
                subjectDictionary = spo[s]
                for p in subjectDictionary.keys():
                    for o in subjectDictionary[p].keys():
                        yield self.intToIdentifier((s, p, o))

    def __len__(self):
        #@@ optimize
        return self.count
        i = 0
        for triple in self.triples((None, None, None)):
            i += 1
        return i


import random

def randid(randint=random.randint, choice=random.choice, signs=(-1,1)):
    return choice(signs)*randint(1,2000000000)

del random
