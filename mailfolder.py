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
from BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Acquisition import aq_parent
from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from utils import uniqueId, makeId, md5Hash, decodeHeader
from Products.CPSMailAccess.mailmessage import MailMessage
from interfaces import IMailFolder, IMailMessage, IMailBox
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner
from Products.Five import BrowserView
from Products.CPSMailAccess.baseconnection import ConnectionError

class MailContainerError(Exception) :
    pass

class MailFolder(BTreeFolder2):
    """A container of mail messages and other mail folders.

    A MailFolder implements IMailFolder:

    >>> f = MailFolder()
    >>> IMailFolder.providedBy(f)
    True
    """
    implements(IMailFolder)
    meta_type = "CPSMailAccess Folder"
    server_name = ''
    sync_state = False

    def __init__(self, uid=None, server_name='""', **kw):
        """
        >>> f = MailFolder('ok', 'Open.INBOX.Stuffs')
        >>> f.getServerName()
        'Open.INBOX.Stuffs'
        """
        BTreeFolder2.__init__(self, uid)
        self.setServerName(server_name)
        self.title = server_name

    def getKeysSlice(self, key1, key2):
        """Get a slice of BTreeFolder2 keys.

        Returns the keys between key1 and key2.
        """
        return self._tree.keys(key1, key2)

    def getValuesSlice(self, key1, key2):
        """Get a slice of BTreeFolder2 objects.

        Returns the objects between key1 and key2.
        """
        return [self[k] for k in self.getKeysSlice(key1, key2)]


    def getMailBox(self):
        """See interfaces.IMailFolder
        """
        current = self
        while current is not None and not IMailBox.providedBy(current):
            current = aq_inner(aq_parent(current))
        return current

    def getMailMessages(self, list_folder=True, list_messages=True,
                        recursive=False):
        """See interfaces.IMailFolder

        >>> f = MailFolder()
        >>> f.getMailMessages()
        []
        """
        results = []

        if list_folder:
            # use btree slices
            r1 = self.getValuesSlice(' ', '-\xff') # '-' is before '.'
            r2 = self.getValuesSlice('/', '\xff') # '/' is after '.'
            folders = list(r1) + list(r2)

            if recursive:
                for folder in folders:
                    results.append(folder)
                    subresults = folder.getMailMessages(list_folder,
                                                        list_messages,
                                                        recursive)
                    results.extend(subresults)
            else:
                results.extend(folders)

        if list_messages:
            # use btree slices
            r = self.getValuesSlice('.', '.\xff')
            results.extend(list(r))

        return results

    def getMailMessagesCount(self, count_folder=True,
                             count_messages=True, recursive=False):
        """See interfaces.IMailFolder

        >>> f = MailFolder()
        >>> f.getMailMessagesCount()
        0
        >>> f.getMailMessagesCount(True, False)
        0
        >>> f.getMailMessagesCount(False, True)
        0
        """
        count = 0

        if recursive:
            # use btree slices
            r1 = self.getValuesSlice(' ', '-\xff') # '-' is before '.'
            r2 = self.getValuesSlice('/', '\xff') # '/' is after '.'
            folders = list(r1) + list(r2)

            if count_folder:
                count += len(folders)

            for folder in folders:
                subcount = folder.getMailMessagesCount(count_folder,
                                                       count_messages,
                                                       recursive)
                count += subcount

        elif count_folder:
            # use btree slices
            r1 = self.getKeysSlice(' ', '-\xff') # '-' is before '.'
            r2 = self.getKeysSlice('/', '\xff') # '/' is after '.'
            count += len(r1) + len(r2)

        if count_messages:
            # use btree slices
            r = self.getKeysSlice('.', '.\xff')
            count += len(r)

        return count

    def getServerName(self):
        """See interfaces.IMailFolder
        """
        return self.server_name

    def setServerName(self, server_name):
        """See interfaces.IMailFolder
        >>> f = MailFolder()
        >>> f.setServerName('INBOX.trash')
        >>> f.getServerName()
        'INBOX.trash'
        """
        # useful if we need some action when renaming server_name
        # typically resync
        self.server_name = server_name

    def getIdFromUid(self, uid):
        """Get the Zope id used to store a message"""
        return '.'+uid

    def _addMessage(self, uid, digest):
        """See interfaces.IMailFolder
        """
        id = self.getIdFromUid(uid)
        msg = MailMessage(id, uid, digest)
        self._setObject(id, msg)
        msg = self._getOb(id)
        return msg

    def _addFolder(self, uid='', server_name=''):
        """see interfaces.IMailFolder
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

    def findMessageByUid(self, uid):
        """ See interfaces.IMailFolder
        """
        id = self.getIdFromUid(uid)
        try:
            msg = self[id]
        except KeyError:
            return None
        if not IMailMessage.providedBy(msg):
            return None
        return msg

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

    def _createKey(self, header):
        """ creates unique key
            for messages identification
        """
        s = ''.join(header.values())
        return md5Hash(s)

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
            uids = connector.search(self.server_name, None,'ALL')
        except ConnectionError:
            # XXX should be a more specific exception (no such dir)
            # this will happen if the directory has been
            # deleted form the server
            uids = []

        for uid in uids:

            msg = self.findMessageByUid(uid)
            if msg is None:
                continue

            msg_headers = connector.fetch(self.server_name, uid,
                                          '(RFC822.HEADER)')
            digest = self._createKey(msg_headers)

            msg = mail_cache.get(digest, remove=True)

            if msg is None:
                # Message is not in cache

                # XXX Only simplest case where all message is cached
                msg_content = connector.fetch(self.server_name, uid,
                                              '(RFC822)')
                # XXX should be done by fetch
                if msg_content and msg_content[0] == 'OK':
                    raw_msg = msg_content[1]
                else:
                    raw_msg = ''

                log.append('adding message %s in %s' % (uid, self.server_name))
                msg = self._addMessage(uid, digest)
                msg.loadMessage(raw_msg)

                #setattr(msg, header, msg_headers[header])
                if msg_headers.has_key('Subject'):
                    msg.title = msg_headers['Subject']

            else:
                # Message was in cache, adding it to self
                log.append('moving message %s in %s' % (uid, self.server_name))
                self._setObject(msg.getId(), msg)

            msg.setSyncState(state=True)

        # now clear messages in zodb that appears to be
        # deleted from the directory
        # and put them in the cache
        for message in zodb_messages:
            if not message.sync_state:
                digest = message.digest
                if not mail_cache.has_key(digest):
                    log.append('adding %s message ni cache' % message.uid)
                    mail_cache[digest] = message
                self.manage_delObjects([message.getId()])
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

#
# MailFolderView Views
#
class MailFolderView(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def sortFolderContent(self, elements):
        """ sorts the content
            so folder gets on top
        """
        sorted_elements = []
        i = 0
        for element in elements:
            if IMailFolder.providedBy(element):
                sorted_elements.append(('A'+str(i), element))
            else:
                sorted_elements.append(('B'+str(i), element))
            i+=1
        sorted_elements.sort()
        results = []
        for element in sorted_elements:
            results.append(element[1])
        return results

    def renderMailList(self):
        """ renders mailfolder content
            XXX need to externalize html here
        """
        mailfolder = self.context

        returned = '<div id="folder_content">'
        elements = mailfolder.getMailMessages(list_folder=True,
            list_messages=True, recursive=False)

        elements = self.sortFolderContent(elements)

        for element in elements:

            returned += '<div id="folder_element">'
            returned += '<a href="%s/view">' % element.absolute_url()
            ob_title = element.title_or_id()

            if ob_title is None:
                mail_title = '?'
            else:
                if IMailMessage.providedBy(element):
                    translated_title = decodeHeader(ob_title)
                    mail_title = translated_title
                else:
                    mail_title = ob_title
            returned += str(mail_title)
            returned += '</a>'
            returned += '</div>'
        returned += '</div>'
        return returned

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
