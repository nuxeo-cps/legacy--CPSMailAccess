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
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from utils import uniqueId, makeId, md5Hash, decodeHeader, getFolder
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailexceptions import MailContainerError
from interfaces import IMailFolder, IMailMessage, IMailBox
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner, aq_base
from Products.Five import BrowserView
from baseconnection import ConnectionError

has_connection = 1

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
    mailbox = None
    message_count = 0
    folder_count = 0

    def __init__(self, uid=None, server_name='""', **kw):
        """
        >>> f = MailFolder('ok', 'Open.INBOX.Stuffs')
        >>> f.getServerName()
        'Open.INBOX.Stuffs'
        """
        BTreeFolder2.__init__(self, uid)
        self.setServerName(server_name)
        self.title = self.simpleFolderName()

    def getNextMessageUid(self):
        """ retrieves next id for messages
            XXX todo : do not calculate it each time
        """
        msgs = self.getMailMessages(list_folder=False, list_messages=True,
            recursive=False)
        highest_id = 0
        for msg in msgs:
            uid = int(msg.uid)
            if uid > highest_id:
                highest_id = uid
        return str(highest_id + 1)

    def clearMailBoxTreeViewCache(self):
        """ clears mailbox cache in case of change
        """
        if self.mailbox is None:
            self.mailbox = self.getMailBox()
        if self.mailbox is not None:
            self.mailbox.clearTreeViewCache()

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

    def hasKey(self, key):
        return len(self.getKeysSlice(key, key)) == 1

    def getMailBox(self):
        """See interfaces.IMailFolder
        """
        current = self
        while current is not None and not IMailBox.providedBy(current):
            current = aq_inner(aq_parent(current))
        """
        if current is None or not IMailBox.providedBy(current):
            raise MailContainerError('object not contained in a mailbox')
        """
        return current

    def getMailFolder(self):
        return self.aq_inner.aq_parent

    def getCacheLevel(self):
        """ returns cache level
        """
        mailbox = self.getMailBox()
        return mailbox.connection_params['cache_level']


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
            if count_folder:
                count += self.folder_count
            # use btree slices
            r1 = self.getValuesSlice(' ', '-\xff') # '-' is before '.'
            r2 = self.getValuesSlice('/', '\xff') # '/' is after '.'
            folders = list(r1) + list(r2)
            for folder in folders:
                subcount = folder.getMailMessagesCount(count_folder,
                                                       count_messages,
                                                       recursive)
                count += subcount
        elif count_folder:
            count += self.folder_count
        if count_messages:
            count += self.message_count
        return count

    def getFlaggedMessageList(self, flags=[]):
        """ returns a list according to given flags
        """
        msgs = self.getMailMessages(list_folder=False,
            list_messages=True, recursive=False)

        msg_list = []

        # opti : 'read' is the most common call
        if len(flags) == 1 and flags[0] == 'read':
            for msg in msgs:
                if msg.read:
                    msg_list.append(msg)
            return msg_list


        for msg in msgs:
            cond1 = 'read' in flags and msg.read
            cond2 = 'answered' in flags and msg.answered
            cond3 = 'deleted' in flags and msg.deleted
            cond4 = 'flagged' in flags and msg.flagged
            cond5 = 'forwarded' in flags and msg.forwarded
            if cond1 and cond2 and cond3 and cond4 and cond5:
                msg_list.append(msg)
        return msg_list


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
        if uid[0] != '.':
            return '.'+uid
        else:
            return uid

    def _moveMessage(self, uid, to_mailbox):
        """ moves the message to another mailbox
        """
        self.clearMailBoxTreeViewCache()
        id = self.getIdFromUid(uid)
        if not hasattr(self, id):
            return None
        msg = self[id]
        # detach message
        self._delObject(id)
        self.message_count -= 1
        # get its new id and uid
        uid = to_mailbox.getNextMessageUid()
        id = to_mailbox.getIdFromUid(uid)
        # free the object from its aquisition
        msg = aq_base(msg)
        msg.uid = uid
        msg.id = id
        #link it to the newmailbox
        to_mailbox._setObject(id, msg)
        to_mailbox.message_count += 1
        msg = getattr(to_mailbox, id)
        return msg

    def _deleteMessage(self, uid):
        """ see interfaces ImailFolder
        """
        self.clearMailBoxTreeViewCache()
        id = self.getIdFromUid(uid)
        if hasattr(self, id):
            msg = self[id]
            self.manage_delObjects([id])
            self.message_count -=1
            #msg = msg.__of__(None)
            return True
        return False

    def _addMessage(self, uid, digest):
        """See interfaces.IMailFolder
        """
        self.clearMailBoxTreeViewCache()
        self.message_count +=1
        id = self.getIdFromUid(uid)
        msg = MailMessage(id, uid, digest)
        self._setObject(id, msg)

        ### ask florent if this is ok with
        # zope 2 and zope 3 compatibilities
        msg.parent_folder = self
        msg = self._getOb(id)
        return msg

    def _addFolder(self, uid='', server_name='', server=False):
        """see interfaces.IMailFolder
        """
        self.clearMailBoxTreeViewCache()
        self.folder_count +=1
        if uid == '':
            uid = uniqueId(self, 'folder_', use_primary=False)
        else:
            uid = makeId(uid)
        if server_name == '':
            server_name = uid
        new_folder = MailFolder(uid, server_name)
        new_id = new_folder.getId()
        self._setObject(new_id, new_folder)
        new_folder = self[new_id]

        if server:
            connector = self._getconnector()
            # todo : look at the result
            connector.create(new_folder.server_name)

        return new_folder

    def findMessageByUid(self, uid):
        """ See interfaces.IMailFolder
        """
        id = self.getIdFromUid(uid)
        try:
            msg = self[id]
        except KeyError:
            return None
        #XXXXXXX ????
        # tests failson this :  providedBy does not work with the fake envs
        #if not IMailMessage.providedBy(msg):
        #    return None
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
        cache_level = self.getCacheLevel()
        mail_cache = mailbox.mail_cache
        connector = self._getconnector()
        zodb_messages = self.getMailMessages(list_folder=False,
            list_messages=True, recursive=False)
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

            if msg is not None:
                msg.setSyncState(state=True)
                continue

            # gets flags, size and headers
            fetched = connector.fetch(self.server_name, uid,\
                '(FLAGS RFC822.SIZE RFC822.HEADER)')

            msg_flags = fetched[0]
            msg_size = fetched[1]
            msg_headers = fetched[2]

            digest = self._createKey(msg_headers)
            msg = mail_cache.get(digest, remove=True)

            if msg is None:
                # Message is not in cache
                if cache_level == 0:
                    # nothing is uploaded
                    # XXX todo
                    raise NotImplementedError
                elif cache_level == 1:
                    # we already have headers
                    # XXX 'OK' should be done by fetch into connection object
                    # we need here to give to the message the number of parts
                    # so it can create them with none
                    #msg_content = ('OK', msg_headers)
                    ####TODO :
                    raw_msg = msg_headers
                    # need to fetch number of part here
                    #and to use it to initiate create empty parts
                    body_structure = connector.fetch(self.server_name, uid, '(BODYSTRUCTURE)')
                else:
                    # XXX Only simplest case where all message is cached
                    # we also get flags
                    #try:
                    msg_content = connector.fetch(self.server_name, uid,
                                                '(FLAGS RFC822)')
                    msg_flags = msg_content[0]
                    msg_body = msg_content[1]
                    #except Timeout:
                    #except:
                        # XXX will be moved to connection object
                    #    msg_content = ''

                # XXX should be done by fetch into connection object
                #raise str(msg_content)

                    if msg_content:
                        raw_msg = msg_body
                    else:
                        raw_msg = ''

                log.append('adding message %s in %s' % (uid, self.server_name))
                msg = self._addMessage(uid, digest)
                # todo: parse flags
                msg.loadMessage(raw_msg, cache_level)
            else:
                # Message was in cache, adding it to self
                log.append('moving message %s in %s' % (uid, self.server_name))
                self._setObject(msg.getId(), msg)
            msg.setSyncState(state=True)
            LOG('sync', INFO, str(uid))

        # now clear messages in zodb that appears to be
        # deleted from the directory
        # and put them in the cache
        for message in zodb_messages:
            if not message.sync_state:
                digest = message.digest
                if not mail_cache.has_key(digest):
                    log.append('adding %s message in cache' % message.uid)
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
            raise MailContainerError('object is not contained in a mailbox')

    def isEmpty(self):
        """ returns True if empty
        """
        return self.getMailMessagesCount(count_folder=True, count_messages=True, \
            recursive=False) == 0

    def rename(self, new_name, fullname=0):
        """ renames the box
        """
        self.clearMailBoxTreeViewCache()
        oldmailbox = self.server_name

        if str(fullname)=='0':
            if oldmailbox.find('.')>1:
                prefix = oldmailbox.split('.')
                del prefix[len(prefix)-1]
                newmailbox = new_name.replace('.', '_')
                newmailbox = '.'.join(prefix) + '.' + newmailbox
            else:
                newmailbox = new_name.replace('.', '_')
        else:
            newmailbox = new_name

        newmailbox = newmailbox.replace('CPS Portal', 'INBOX')

        if has_connection:
            connector = self._getconnector()
            server_rename = connector.rename(oldmailbox, newmailbox)
            if not server_rename:
                # TODO :raise an error
                return False

        # now zodb renaming :
        # first of all, let's detach the folder
        # from its parent

        #XX detach from parent
        parent = self.getMailFolder()
        parent._delObject(self.id)
        parent.folder_count -= 1
        gparent = parent.getMailFolder()
        while gparent is not None and IMailFolder.providedBy(gparent):
            gparent.folder_count -= 1
            gparent = gparent.getMailFolder()

        # let's find the new parent
        if newmailbox.find('.')>-1:
            path = newmailbox.split('.')
            basename = path[len(path)-1]
            del path[len(path)-1]
        else:
            path = []
            basename = newmailbox

        current = self.getMailBox()
        for node in path:
            current = getattr(current, node)

        # make the folder free
        self = aq_base(self)
        self.id = makeId(basename)

        # let's append the folder to this new parent
        current._setObject(self.id, self)
        current.folder_count += 1
        parent = current.getMailFolder()
        while parent is not None and IMailFolder.providedBy(parent):
            parent.folder_count += 1
            parent = parent.getMailFolder()

        self = getattr(current, self.id)

        # recreating server name
        if fullname==0:
            self.server_name = newmailbox
        else:
            self.server_name = new_name

        self.title = self.id
        return self

    def delete(self):
        """ sends the mailbox to the thrash
            by renaming it
        """
        mailbox = self.getMailBox()
        trash_folder_name = mailbox.getTrashFolderName()
        trash = mailbox.getTrashFolder()
        # verify the name
        seed = 1
        name = self.simpleFolderName()
        composed = name
        while trash.hasKey(composed):
            composed = name + '_' +str(seed)
            seed += 1
        newmailbox = trash_folder_name + '.' + composed
        return self.rename(newmailbox, fullname=True)

    def simpleFolderName(self):
        """ retrieves the simple folder name
        """
        fullname = self.server_name
        prefix = fullname.split('.')
        return prefix[len(prefix)-1]

    def copy(self, copy_name):
        """ copy a mailbox into another one
        """
        # TODO
        raise NotImplementedError

    def moveMessage(self, uid, new_mailbox):
        """ moves the message on the server,
            then on the zodb (no sync)
        """
        mailbox = self.getMailBox()

        trash_name = mailbox.getTrashFolderName()
        if has_connection:
            connector = self._getconnector()
            res = connector.copy(self.server_name, trash_name, uid)
            if not res:
                return False
        # XXX todo : check if is the same msg uid
        trash = mailbox.getTrashFolder()
        return self._moveMessage(uid, trash) is not None


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
    if IMailFolder.providedBy(container):
        container.folder_count += 1
    container._setObject(ob.getId(), ob)
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')
