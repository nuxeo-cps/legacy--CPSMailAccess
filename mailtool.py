# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziadé <tz@nuxeo.com>
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
#
"""
  mailtool contains singleton tool used to
  hold connections and to hold
"""
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.utils import UniqueObject
from interfaces import IMailTool
from Globals import InitializeClass
from zope.interface import implements
from Products.CPSMailAccess.connectionlist import registerConnections,\
     ConnectionList

class MailTool(Folder, UniqueObject):
    """ the portal tool wich holds
        several parameters and connections

        A MailTool implements IMailTool:

    >>> f = MailTool()
    >>> IMailTool.providedBy(f)
    True
    """
    implements(IMailTool)
    meta_type = "CPSMailAccess Tool"
    id = 'portal_webmail'

    _v_connection_list = ConnectionList()

    def __init__(self):
        self._initializeConnectionList()


    def _initializeConnectionList(self):
        """ registers all access plugins
        """
        registerConnections(self._v_connection_list)

    def listConnectionTypes(self):
        """ see IMailTool
        """
        return self._v_connection_list.listConnectionTypes()

    def reloadPlugins(self):
        """ see IMailTool
        """
        self._initializeConnectionList()

    def getConnection(self, connection_type):
        """ see IMailTool
        """
        return self._v_connection_list.getConnection(connection_type)

""" classic Zope 2 interface for class registering
"""
InitializeClass(MailTool)

manage_addMailToolForm = PageTemplateFile(
    "www/zmi_addmailtool", globals())

def manage_addMailTool(container, REQUEST=None, **kw):
    """ Add a portal_webmail to the portal
    >>> from OFS.Folder import Folder
    >>> f = Folder()
    >>> manage_addMailTool(f)
    >>> f.portal_webmail.getId()
    'portal_webmail'
    """
    container = container.this()
    ob = MailTool(**kw)
    container._setObject(ob.getId(), ob)
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')
