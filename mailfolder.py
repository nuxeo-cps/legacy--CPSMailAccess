# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziadé <tz@nuxeo.com>
#          Florent Guillaume <tz@nuxeo.com>
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
"""MailFolder

A MailFolder contains mail messages and other mail folders.
"""
from zLOG import LOG, DEBUG, INFO
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from Acquisition import aq_parent
from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from utils import uniqueId, makeId, md5Hash
from Products.CPSMailAccess.mailmessage import MailMessage
from interfaces import IMailFolder, IMailMessage, IMailBox
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner

from Products.CPSMailAccess.baseconnection import ConnectionError

class MailContainerError(Exception) :
    pass

class MailFolder(Folder):
    """A container of mail messages and other mail folders.

    A MailFolder implements IMailFolder:

    >>> f = MailFolder()
    >>> IMailFolder.providedBy(f)
    True
    """
    ### XXX see if "properties" are ok in zope3/five context
    _properties = Folder._properties + \
        ({'id': 'server_name', 'type': 'string', 'mode': 'w',
         'label': 'Server name'},)

    meta_type = "CPSMailAccess Folder"

    implements(IMailFolder)
    server_name = FieldProperty(IMailFolder['server_name'])
    mail_prefix = FieldProperty(IMailFolder['mail_prefix'])

    sync_state = False

    def __init__(self, uid=None, server_name='""', **kw):
        """
        >>> f = MailFolder('ok', 'Open.INBOX.Stuffs')
        >>> f.getServerName()
        'Open.INBOX.Stuffs'
        """
        Folder.__init__(self, uid)
        self.mail_prefix = 'msg_'
        self.setServerName(server_name)
        self.title = server_name

    def getMailBox(self):
        """See interfaces.IMailFolder
        """
        current = self
        while current is not None and not IMailBox.providedBy(current):
            current = aq_parent(current)
        return current

    def getMailMessages(self, list_folder=True, list_messages=True, recursive=False):
        """See interfaces.IMailFolder

        >>> f = MailFolder()
        >>> f.getMailMessages()
        []
        """
        providers = ()
        result = []

        if list_folder:
            providers = providers+ (IMailFolder,)

        if list_messages:
            providers = providers+ (IMailMessage,)

        for element in self.objectValues():
            for provider in providers :
                if provider.providedBy(element):
                    # see ***
                    result.insert(0, provider(element))

            if recursive:
                if IMailFolder.providedBy(element):
                    sub_folder = element.getMailMessages(list_folder,
                        list_messages, recursive)

                    # *** we rather insert messages in front
                    # of the list, rather than extending it
                    # for speed reasons so when elements are deleted,
                    # a child gets found before its parent
                    for element in sub_folder:
                        result.insert(0, element)

        return result

    def getMailMessagesCount(self, count_folder=True, count_messages=True, recursive=False):
        """See interfaces.IMailFolder
        examples of calls :
        >>> f = MailFolder()
        >>> f.getMailMessagesCount()
        0
        >>> f.getMailMessagesCount(True, False)
        0
        >>> f.getMailMessagesCount(False, True)
        0
        """
        providers = ()

        if count_folder:
            providers = providers+ (IMailFolder,)

        if count_messages:
            providers = providers+ (IMailMessage,)

        count = 0

        if len(providers) > 0:
            for element in self.objectValues():
                for provider in providers :
                    if provider.providedBy(element):
                        count += 1
                if recursive:
                    if IMailFolder.providedBy(element):
                        count += element.getMailMessagesCount(count_folder,
                            count_messages, recursive)
        return count

    def getServerName(self):
        """"See interfaces.IMailFolder
        """
        return self.server_name

    def setServerName(self, server_name):
        """"See interfaces.IMailFolder
        >>> f = MailFolder()
        >>> f.setServerName('INBOX.trash')
        >>> f.getServerName()
        'INBOX.trash'
        """
        # useful if we need some action when renaming server_name
        # typically resync
        self.server_name = server_name

    def _addMessage(self, msg_uid='', msg_key=''):
        """"See interfaces.IMailFolder
        """
        uid = uniqueId(self, self.mail_prefix)
        new_msg = MailMessage(uid, msg_uid, msg_key)

        self._setObject(new_msg.getId(), new_msg)
        new_msg = self._getOb(new_msg.getId())

        return new_msg

    def _addFolder(self, uid='', server_name=''):
        """"See interfaces.IMailFolder
        """
        if uid == '':
            uid = uniqueId(self, 'folder_', use_primary=False)
        else:
            uid = makeId(uid)

        if server_name == '':
            server_name = uid

        new_folder = MailFolder(uid, server_name)
        self._setObject(new_folder.getId(), new_folder)
        new_folder = self._getOb(new_folder.getId())

        return new_folder

    def findMessage(self, msg_key, recursive=True):
        """ See interfaces.IMailFolder
        """
        # XXX see for caching here
        message_list = self.getMailMessages(list_folder=False, list_messages=True, \
            recursive=recursive)

        for message in message_list:
            if message.msg_key == msg_key:
                return message

        return None

    def findMessageByUid(self, msg_uid, recursive=True):
        """ See interfaces.IMailFolder
        """
        # XXX see for caching here
        message_list = self.getMailMessages(list_folder=False, list_messages=True, \
            recursive=recursive)

        for message in message_list:
            if str(message.msg_uid) == str(msg_uid):
                return message

        return None

    def childFoldersCount(self):
        """ See interfaces.IMailFolder
        """
        return self.getMailMessagesCount(count_folder=True, count_messages=False, \
            recursive=False)

    def getchildFolders(self):
        """ See interfaces.IMailFolder
        """
        return self.getMailMessages(list_folder=True, list_messages=False)

    def setSyncState(self, state=False, recursive=False):
        """ sets state
        """
        self.sync_state = state
        if recursive:
            folders = self.getchildFolders()
            for folder in folders:
                folder.setSyncState(state, True)

    def _createKey(self, uid, header):
        """ creates unique key
            for messages identification
        """
        elements = ''
        for key in header.keys():
            elements += str(header[key])
        return md5Hash(str(uid)+elements)

    def _synchronizeFolder(self, return_log=False):
        """ See interfaces.IMailFolder
        """
        log = []
        mailbox = self.getMailBox()
        mail_cache = mailbox.mail_cache
        connector = self._getconnector()
        zodb_messages = self.getMailMessages(False, True, False)
        # now syncing server_folder and current one
        for message in zodb_messages:
            message.setSyncState(state=False)

        try:
            server_messages = connector.search(self.server_name, None,'ALL')
        except ConnectionError:
            # this will happen if the directory has been
            # deleted form the server
            server_messages = []

        for message in server_messages:

            # first of all, search message by uidwich is unique inside a folder
            msg = self.findMessageByUid(message, recursive=False)

            if msg is None:
                # opti : Will do just one call
                #msg_uid = connector.fetch(self.server_name, message, '(UID)')
                #msg_uid = str(msg_uid['UID'])
                msg_uid = str(message)

                msg_headers = connector.fetch(self.server_name, message, '(RFC822.HEADER)')
                msg_key = self._createKey(msg_uid, msg_headers)

                # first of all, search message by key
                #msg = self.findMessage(msg_key, recursive=False)

                # check if the message is in the orphan list
                if msg is None:
                    msg = mail_cache.retrieveMessage(msg_key, remove=True)

                    # the message has to be created
                    if msg is None:
                        log.append('adding message %s in %s' % (msg_uid, self.server_name))
                        msg = self._addMessage(msg_uid, msg_key)

                        # THIS IS A HACK,next step is to create
                        # a message accordingly to the whol message string
                        for header in msg_headers.keys():
                            msg.setParam(header, msg_headers[header])
                            if msg_headers.has_key('Subject'):
                                msg.title = msg_headers['Subject']
                    else:
                        # was in cache, linking it to self
                        log.append('moving message %s in %s' % (msg_uid, self.server_name))
                        self._setObject(msg.getId(), msg)

            if msg:
                msg.setSyncState(state=True)

        # now clear messages in zodb that appears to be
        # deleted from the directory
        # and put them in the cache
        for message in zodb_messages:
            if not message.sync_state:
                if not mail_cache.inCache(message):
                    log.append('adding %s message ni cache' % message.msg_uid)
                    mail_cache.putMessage(message)
                self.manage_delObjects([message.getId(),])
        if return_log:
            return log

    def checkMessages(self):
        """See interfaces.IMailFolder
        """
        raise NotImplementedError

    def _getconnector(self):
        """See interfaces.IMailFolder
        """
        current = self
        while not IMailBox.providedBy(current) and current is not None:
            current = aq_parent(current)

        if current is not None:
            return current._getconnector()
        else:
            raise MailContainerError('%s is not contained in a mailbox' % self.getId())

""" classic Zope 2 interface for class registering
"""
InitializeClass(MailFolder)

manage_addMailFolderForm = PageTemplateFile(
    "www/zmi_addmailfolder", globals())

def manage_addMailFolder(container, id=None, server_name ='',
        REQUEST=None, **kw):
    """Add a box to a container (self).
    >>> from OFS.Folder import Folder
    >>> f = Folder()
    >>> manage_addMailFolder(f, 'inbox')
    >>> f.inbox.getId()
    'inbox'

    """
    container = container.this()
    ob = MailFolder(id, server_name, **kw)
    container._setObject(ob.getId(), ob)
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')
