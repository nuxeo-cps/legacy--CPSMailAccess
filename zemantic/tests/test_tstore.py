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

import unittest
from zope.testing.doctestunit import DocTestSuite

def allTriples(c):
    l =  list(c.triples((None,None,None)))
    l.sort()
    return l

FAUX_RDF_FILE ="""
<rdf:RDF xmlns="http://web.resource.org/cc/"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<Work rdf:about="http://zemantic.org/zemantic/zemantic.py">
</Work> \
</rdf:RDF>
"""

# All one line!
FAUX_NT_FILE = ('<http://zemantic.org/zemantic/zemantic.py> ' 
                '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ' 
                '<http://web.resource.org/cc/Work>.\n' 
               )

def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zemantic.triplestore',
                     extraglobs={'allTriples': allTriples,
                                 'FAUX_RDF_FILE': FAUX_RDF_FILE,
                                 'FAUX_NT_FILE': FAUX_NT_FILE,
                                }),        
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
