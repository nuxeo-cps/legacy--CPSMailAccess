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
<Work rdf:about="http://zemantic.org/zemantic/cataloger.py"
  dc:title="zemantic.cataloger"
  dc:date="2005"
  dc:description="Sample auto-cataloging code.  See examples/library/cataloger.py.">
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
from zope.app.container.interfaces import IObjectAddedEvent
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.app.event.interfaces import IObjectModifiedEvent
from interfaces import IRDFXML, ITripleStore

from StringIO import StringIO

# This is an example cataloger that hooks Zope 3 container events.
# Your application should create their own catalogers for their
# content types so that they can exactly control cataloging.  See
# examples/library/cataloger.py

class Cataloger(object):
    """Class to handle automatic cataloging/uncataloging on container
    events."""

    def __init__(self, iface):
        self._iface = iface

    def __call__(self, event):
        """Called by the event system."""
        if self._iface.providedBy(event.object):
            
            if IObjectAddedEvent.providedBy(event):
                self.handleAdded(event.object)
                
            elif IObjectModifiedEvent.providedBy(event):
                self.handleModified(event.object)
                
            elif IObjectRemovedEvent.providedBy(event):
                self.handleRemoved(event.object)

    def handleAdded(self, object):
        c = zapi.queryUtility(ITripleStore)
        if c is not None:
            pass # add your logic here
    
    def handleModified(self, object):
        c = zapi.queryUtility(ITripleStore)
        if c is not None:
            pass # add your logic here

    def handleRemoved(self, object):
        c = zapi.queryUtility(ITripleStore)
        if c is not None:
            pass # add your logic here


cataloger = Cataloger(ITripleStore)
