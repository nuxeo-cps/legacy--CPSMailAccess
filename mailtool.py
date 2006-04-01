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
import os
import thread

from OFS.Folder import Folder
from ZODB.PersistentMapping import PersistentMapping
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from Products.Five import BrowserView

from zope.interface import implements

from interfaces import IMailTool
from connectionlist import registerConnections, ConnectionList
from smtpmailer import SmtpMailer
from mailbox import manage_addMailBox
from utils import makeId, getMemberById, getToolByName, getAuthenticatedMember

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

# XXX might want to externalize it in a file
default_parameters = {'connection_type' : ('IMAP', 1),
            'HOST' : ('localhost', 1),
            'PORT' : (143, 1),
            'SSL' :  (0, 1),
            'login' : ('', 0),
            'password' :('', 0),
            'smtp_host' : ('localhost', 1),
            'smtp_port' : (25, 1),
            'trash_folder_name' : ('INBOX.Trash', 1),
            'draft_folder_name' : ('INBOX.Drafts', 1),
            'sent_folder_name' : ('INBOX.Sent', 1),
            'max_folder_size' : (20, 1),
            'max_folder_depth' : (2, 1),
            'treeview_style' : ('lotus', 1),
            'message_list_cols' :
            ('Attachments, Icon, From, Date, Subject, Size', 1),
            'signature' : ('', 0),
            'direct_smtp' : (1, 1),
            'addressbook' : ('addressbook', 1),
            'read_only_folders': ('', 1),
            'protected_folders': ('INBOX.Sent', 1),
            'index_relations': (0, 1),
            'webmail_enabled': ('webmail_enabled:1', -1)
            }

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

    def __init__(self):
        Folder.__init__(self)
        self.__version__ = (1, 0, 0, 'b2')
        self.default_connection_params = PersistentMapping()
        self._initializeParameters()
        self._initializeConnectionList()
        direct_smtp = self.default_connection_params['direct_smtp'][0]

        # creating a temporary directory for mail storage
        temp_dir = os.path.dirname(os.tempnam())
        temp_dir = os.path.join(temp_dir, 'maildir')
        self._maildeliverer = SmtpMailer(temp_dir, direct_smtp,
                                         on_send_mail = '_checkCanSendMails')

    def _checkCanSendMails(self):
        if not self.canHaveMailBox():
            # XXX Z2
            from AccessControl import Unauthorized
            raise Unauthorized('Cannot send mails from this account')

    def getMailDeliverer(self):
        """ check if _maildeliverer points on the right
        folder, if not recreates it"""
        if self.default_connection_params.has_key('maildir'):
            mail_dir = self.default_connection_params['maildir'][0]
            direct_smtp = self.default_connection_params['direct_smtp'][0]
        else:
            mail_dir = None
            direct_smtp = 1

        # recreate in case of changes
        if (self._maildeliverer.maildir_directory != mail_dir or
            self._maildeliverer.direct_smtp != direct_smtp):
            self._maildeliverer = SmtpMailer(mail_dir, direct_smtp,
                                             '_checkCanSendMails')

        return self._maildeliverer

    def _initializeParameters(self):
        """ initialize parameters with default ones """
        global default_parameters
        for key in default_parameters:
            self.default_connection_params[key] = default_parameters[key]

    def getConnectionParams(self):
        return self.default_connection_params

    def setParameters(self, connection_params):
        """ sets the parameters """
        items = self.default_connection_params.items()
        fixed_keys = [key for key, value in items if value[1] == -1]

        for key in connection_params.keys():
            # check for parameters that can't be customized
            # in submailboxes
            if key in fixed_keys:
                self.default_connection_params[key] = \
                    (connection_params[key][0], -1)
            else:
                self.default_connection_params[key] = connection_params[key]

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

    def getConnection(self, connection_params, connection_number=0):
        """ see IMailTool """
        try:
            res = self.getConnectionList().getConnection(connection_params,
                                                         connection_number)
            return res
        except ValueError:
            self.reloadPlugins()
        return self.getConnectionList().getConnection(connection_params,
                                                       connection_number)

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

    def canHaveMailBox(self, user_id=None):
        """ check wheter the user can use the webmail """
        def _compareValues(value1, value2):
            """ compares values

            >>> _compareValues('1', True)
            True
            >>> _compareValues('1', 1)
            True
            >>> _compareValues(1, 1)
            True
            """
            def _normalize(value):
                if isinstance(value, bool):
                    value = str(int(value))
                elif isinstance(value, str):
                    value = int(value)
                return str(value).strip()

            if type(value1) != type(value2):
                value1 = _normalize(value1)
                value2 = _normalize(value2)

            return value1 == value2

        if user_id is None:
            user = getAuthenticatedMember(self)
        else:
            user = getMemberById(self, user_id)

        if user is None:
            return False
        else:
            # XXX Z2:
            webmail_enabled_conf = \
                self.default_connection_params['webmail_enabled'][0]

            parts = webmail_enabled_conf.split(':')
            webmail_enabled_field = parts[0].strip()
            if len(parts) > 1:
                value = parts[1].strip()
            else:
                value = 1

            #XXX assumes and enforces that we have a CPS User Folder
            aclu = self.acl_users
            assert(aclu.meta_type == 'CPS User Folder')
            dtool = getToolByName(self, 'portal_directories')
            mdir = dtool[aclu.users_dir]
            # user can be defined upper in Zope
            try:
                entry = mdir._getEntry(user.getId())
            except KeyError:
                return False
            webmail_enabled = entry.get(webmail_enabled_field, 0)

            if len(value) > 0 and value[0] == '!':
                return not _compareValues(webmail_enabled, value[1:])
            else:
                return _compareValues(webmail_enabled, value)


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
                                           '/syncProgress.html')
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
