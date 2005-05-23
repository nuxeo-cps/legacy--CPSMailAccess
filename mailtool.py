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
import thread

from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from Products.Five import BrowserView

from zope.interface import implements

from interfaces import IMailTool
from connectionlist import registerConnections, ConnectionList
from smtpmailer import SmtpQueuedMailer
from mailbox import manage_addMailBox
from utils import makeId, getMemberById

lock = thread.allocate_lock()
connector = ConnectionList()

def getConnection():
    """
    lock.acquire()
    try:
        return connector
    finally:
        lock.release()
    return None
    """
    return connector

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
    _initialized = 0

    # to be externalized
    maildeliverer = SmtpQueuedMailer()

    default_connection_params = {'connection_type' : 'IMAP',
                                 'HOST' : 'localhost',
                                 'PORT' : 143,
                                 'SSL' :  0,
                                 'login' : '',
                                 'password' :'',
                                 'smtp_host' : 'localhost',
                                 'smtp_port' : 25,
                                 'trash_folder_name' : 'INBOX.Trash',
                                 'draft_folder_name' : 'INBOX.Drafts',
                                 'sent_folder_name' : 'INBOX.Sent',
                                 'max_folder_size' : 20,
                                 'max_folder_depth' : 2,
                                 'treeview_style' : 'lotus',
                                 'message_list_cols' :
                                   'Attachments, Icon, From, Date, Subject, Size',
                                 'signature' : '',
                                }

    def __init__(self):
        Folder.__init__(self)
        self._initializeConnectionList()

    def getConnectionList(self):
        """ connection list getter """
        self._initializeConnectionList()
        return self.connection_list

    def _initializeConnectionList(self):
        """ registers all access plugins """
        if self._initialized == 0:
            registerConnections(self.connection_list)
            self._initialized = 1

    def listConnectionTypes(self):
        """ see IMailTool """
        return self.getConnectionList().listConnectionTypes()

    def reloadPlugins(self):
        """ see IMailTool """
        self._initialized = 0
        self._initializeConnectionList()

    def getConnection(self, connection_params):
        """ see IMailTool """
        try:
            res = self.getConnectionList().getConnection(connection_params)
            return res
        except ValueError:
            self.reloadPlugins()
        return self.getConnectionList().getConnection(connection_params)

    def killConnection(self, uid, connection_type):
        """ kill someone connections """
        self.getConnectionList().killConnection(uid, connection_type)

    def killAllConnections(self):
        """ kill someone connections """
        self.getConnectionList().killAllConnections()

    def addMailBox(self, user_id):
        """ creates a mailbox for a given user """
        mailbox_name = makeId('box_%s' % user_id)
        if hasattr(self, mailbox_name):
            return getattr(self, mailbox_name)
        else:
            box = manage_addMailBox(self, mailbox_name)
            # make sure the box belongs to the user
            user = getMemberById(self, user_id)
            box.changeOwnership(user)
            return box

    def deleteMailBox(self, user_id):
        """ deletes the mailbox for a given user """
        mailbox_name = makeId('box_%s' % user_id)
        if hasattr(self, mailbox_name):
            self.manage_delObjects([mailbox_name])

    def hasMailBox(self, user_id):
        """ creates a mailbox for a given user """
        mailbox_name = makeId('box_%s' % user_id)
        return hasattr(self, mailbox_name)

""" classic Zope 2 interface for class registering
"""
InitializeClass(MailTool)


class MailToolView(BrowserView):

    def webmailRedirect(self, user_id):
        """ redirects the user to his or her webmail """

        if self.request is None:
            return
        mailtool = self.context
        mailbox_name = makeId('box_%s' % user_id)
        if hasattr(mailtool, mailbox_name):
            box = getattr(mailtool, mailbox_name)
            # always synchronize when we get in
            self.request.response.redirect(box.absolute_url()+\
                                           '/syncProgress.html?g_user='+\
                                           user_id)
        else:
            box = mailtool.addMailBox(user_id)
            url = '%s/configure.html?first_time=1' % box.absolute_url()
            self.request.response.redirect(url)

    def reloadPlugins(self):
        """ reload plugins"""
        mailtool = self.context
        mailtool.reloadPlugins()
        rendered = ['plugins:']
        rendered.extend(mailtool.listConnectionTypes())
        rendered.append('end of list.')
        return '\n'.join(rendered)

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
