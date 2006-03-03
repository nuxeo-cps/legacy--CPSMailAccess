# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
# $Id$
""" CPSMailAccess XML Adapter.
"""
from Acquisition import aq_base
from xml.dom.minidom import Element

from zope.component import adapts
from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron

from Products.CPSDocument.exportimport import exportCPSObjects
from Products.CPSDocument.exportimport import importCPSObjects

from Products.CPSMailAccess.interfaces import IMailTool

_marker = object()

TOOL = 'portal_webmail'
NAME = 'webmail'

def exportCPSMailAccess(context):
    """Export user folder configuration as a set of XML files.

    Does not export the users themselves.
    """
    site = context.getSite()
    if getattr(aq_base(site), TOOL, None) is None:
        logger = context.getLogger(NAME)
        logger.info("Nothing to export.")
        return
    tool = getToolByName(site, TOOL)
    exportCPSObjects(tool, '', context)

def importCPSMailAccess(context):
    """Import user folder configuration from XML files.
    """
    site = context.getSite()
    if getattr(aq_base(site), TOOL, None) is None:
        logger = context.getLogger(NAME)
        logger.info("Cannot import into missing acl_users.")
        return
    tool = getToolByName(site, TOOL)
    importCPSObjects(tool, '', context)


class CPSMailAccessXMLAdapter(XMLAdapterBase, ObjectManagerHelpers):
    """XML importer and exporter for portal_webmail
    """

    adapts(IMailTool, ISetupEnviron)
    implements(IBody)
    _LOGGER_ID = NAME
    name = NAME

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractCPSMailAccessProperties())
        node.appendChild(self._extractObjects())
        self._logger.info("CPSMailAccess exported.")
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        meta_type = str(node.getAttribute('meta_type'))
        if meta_type != self.context.meta_type:
            self._logger.error("Cannot import %r into %r." %
                               (meta_type, self.context.meta_type))
            return
        if self.environ.shouldPurge():
            self._purgeCPSMailAccessProperties()
            # XXX need to purge just .cpsportlets
            # and not existing BALs
            self._purgeObjects()

        self._initCPSMailAccessProperties(node)
        self._initObjects(node)
        self._logger.info("CPSMailAccess imported.")

    node = property(_exportNode, _importNode)

    def _sequenceToXML(self, root, sequence):
        values = self._doc.createElement('values')
        for element in sequence:
            value = self._doc.createElement('value')
            value_content = self._doc.createTextNode(str(element))
            value.appendChild(value_content)
            value.setAttribute('type', type(element).__name__)
            values.appendChild(value)
        root.appendChild(values)

    def _XMLToSequence(self, root):
        def _changeType(value, type_):
            if type_ == 'int':
                return int(value)
            if type_ == 'float':
                return float(value)
            return value

        sequence = []
        for child in root.childNodes:
            if not isinstance(child, Element):
                continue
            type_ = child.getAttribute('type')
            value = self._getNodeText(child)
            sequence.append(_changeType(value, type_))
        return sequence

    def _extractCPSMailAccessProperties(self):
        portal_webmail = self.context
        fragment = self._doc.createDocumentFragment()
        elements = portal_webmail.default_connection_params.items()
        # we want a fixed order
        elements.sort()
        for key, values in elements:
            child = self._doc.createElement('parameter')
            child.setAttribute('name', key)
            self._sequenceToXML(child, values)
            fragment.appendChild(child)
        return fragment

    def _purgeCPSMailAccessProperties(self):
        return

    def _initCPSMailAccessProperties(self, node):
        portal_webmail = self.context
        loaded_params = {}

        for child in node.childNodes:
            if child.nodeName != 'parameter':
                continue
            name = child.getAttribute('name')
            children = [elmt for elmt in child.childNodes
                        if isinstance(elmt, Element)]
            values = self._XMLToSequence(children[0])
            loaded_params[name] = tuple(values)

        portal_webmail.default_connection_params = loaded_params
