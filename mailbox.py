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
# $Id$
"""MailBox

A MailBox is the root MailFolder for a given mail account
"""
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from utils import uniqueId, makeId
from Products.CPSMailAccess.interfaces import IMailBox, IMapping
from Products.CPSMailAccess.mailfolder import MailFolder
from interfaces import IMailFolder, IMailMessage
from Globals import InitializeClass
from zope.schema.fieldproperty import FieldProperty

### see for CMF dependency here
from Products.CMFCore.utils import getToolByName

class MailBox(MailFolder):
    """ the main container

    >>> f = MailBox()
    >>> IMailFolder.providedBy(f)
    True
    >>> IMailBox.providedBy(f)
    True
    >>> IMapping.providedBy(f)
    True
    """
    meta_type = "CPSMailAccess Box"
    portal_type = meta_type

    implements(IMailBox, IMapping)

    # see here for security
    connection_params = FieldProperty(IMailBox['connection_params'])

    def __init__(self, uid=None, server_name='', **kw):
        MailFolder.__init__(self, uid, server_name, **kw)
        self.connection_params = {}

    def synchronize(self):
        """ see interface
        """
        sub_folders = self.getMailMessages(list_folder=True, list_messages=False,
            recursive=True)

        for sub_folder in sub_folders:
            sub_folder._synchronizeFolder()

        self._synchronizeFolder()

    def _getconnector(self):
        """get mail server connector
        """
        wm_tool = getToolByName(self, 'portal_webmail')
        if wm_tool is None:
            raise ValueError(MISSING_TOOL)

        # safe scan in case of first call
        if wm_tool.listConnectionTypes() == []:
            wm_tool.reloadPlugins()

        connection_params = self.connection_params

        try:
            connector = wm_tool.getConnection(connection_params)
        except ConnectionError:
            # TODO : we need to redirect here to a clean
            # "login failed" screen
            raise ValueError(BAD_LOGIN)

        if connector is None:
            raise ValueError(NO_CONNECTOR)

        return connector

    #
    # MAPPING INTERFACE for connection params internal dict. (partial)
    #
    # this is used to catch property changes that might
    # need to call some actions
    def __len__(self):
        """ see interface
        """
        return len(self.connection_params)

    def __getitem__(self, name):
        """ see interface
        """
        return self.connection_params[name]

    def __setitem__(self, name, val):
        """ see interface
        """
        self.connection_params[name] = val

    def __delitem__(self, name):
        """ see interface
        """
        del self.connection_params[name]

    def has_key(self, name):
        """ see interface
        """
        return self.connection_params.has_key(name)

    def keys(self):
        """ see interface
        """
        return self.connection_params.keys()

    def values(self):
        """ see interface
        """
        return self.connection_params.values()

    def items(self):
        """ see interface
        """
        return self.connection_params.items()

""" classic Zope 2 interface for class registering
"""
InitializeClass(MailBox)

manage_addMailBoxForm = PageTemplateFile(
    "www/zmi_addmailbox", globals())

def manage_addMailBox(container, id=None, server_name ='',
        REQUEST=None, **kw):
    """Add a box to a container (self).
    >>> from OFS.Folder import Folder
    >>> f = Folder()
    >>> manage_addMailBox(f, 'mails')
    >>> f.mails.getId()
    'mails'
    """
    container = container.this()
    ob = MailBox(id, server_name, **kw)
    container._setObject(ob.getId(), ob)
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')

