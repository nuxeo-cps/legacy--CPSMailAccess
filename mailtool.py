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
#from Products.CMFCore.utils import UniqueObject
from interfaces import IMailTool
from Globals import InitializeClass
from zope.interface import implements
from Products.CPSMailAccess.connectionlist import registerConnections,\
     ConnectionList
import thread
from Products.Five import BrowserView
from smtpmailer import SmtpQueuedMailer
from mailbox import manage_addMailBox
from utils import makeId

lock = thread.allocate_lock()
connector = ConnectionList()

def getConnection():
    lock.acquire()
    try:
        return connector
    finally:
        lock.release()

class MailTool(Folder): # UniqueObject
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
    connection_list = getConnection()
    initialized = 0
    # to be externalized
    maildeliverer = SmtpQueuedMailer()

    def __init__(self):
        Folder.__init__(self)
        self._initializeConnectionList()

    def getConnectionList(self):
        """ connection list getter
        """
        #if self.initialized <> 1:
        self._initializeConnectionList()
        return self.connection_list

    def _initializeConnectionList(self):
        """ registers all access plugins
        """
        registerConnections(self.connection_list)
        self.initialized = 1

    def listConnectionTypes(self):
        """ see IMailTool
        """
        return self.getConnectionList().listConnectionTypes()

    def reloadPlugins(self):
        """ see IMailTool
        """
        self._initializeConnectionList()

    def getConnection(self, connection_params):
        """ see IMailTool
        """
        return self.getConnectionList().getConnection(connection_params)

    def killConnection(self, uid, connection_type):
        """ kill someone connections
        """
        self.getConnectionList().killConnection(uid, connection_type)

    def killAllConnections(self):
        """ kill someone connections
        """
        self.getConnectionList().killAllConnections()

    def addMailBox(self, user_id):
        """ creates a mailbox for a given user """

        mailbox_name = makeId('box_%s' % user_id)
        if hasattr(self, mailbox_name):
            return getattr(self, mailbox_name)
        else:
            return manage_addMailBox(self, mailbox_name)

    def deleteMailBox(self, user_id):
        """ deletes the mailbox for a given user """

        mailbox_name = makeId('box_%s' % user_id)
        if hasattr(self, mailbox_name):
            self.manage_delObjects([mailbox_name])


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
