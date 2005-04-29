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
import time
from zLOG import LOG, DEBUG, INFO
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner, aq_base
from Products.Five import BrowserView

from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from zope.app.cache.ram import RAMCache

from mailmessage import MailMessage
from mailexceptions import MailContainerError
from interfaces import IMailFolder, IMailMessage, IMailBox
from utils import uniqueId, makeId, md5Hash, decodeHeader, getFolder,\
                  AsyncCall
from baseconnection import ConnectionError, has_connection

class MailFolder(BTreeFolder2):
    """A container of mail messages and other mail folders.

    A MailFolder implements IMailFolder:

    >>> f = MailFolder()
    >>> IMailFolder.providedBy(f)
    True
    """
    implements(IMailFolder)
    meta_type = 'CPSMailAccess Folder'
    server_name = ''
    sync_state = False
    mailbox = None
    message_count = 0
    folder_count = 0
    loose_sync = True
    fetch_size = 200
    instant_load = True

    def __init__(self, uid=None, server_name='""'):
        """
        >>> f = MailFolder('ok', 'Open.INBOX.Stuffs')
        >>> f.getServerName()
        'Open.INBOX.Stuffs'
        """
        BTreeFolder2.__init__(self, uid)
        self.setServerName(server_name)
        self.title = self.simpleFolderName()
        self._cache = RAMCache()

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
        """ clears mailbox cache in case of change """
        mailbox = self.getMailBox()
        if mailbox is not None:
            mailbox.clearTreeViewCache()

    def getKeysSlice(self, key1, key2):
        """ Get a slice of BTreeFolder2 keys.

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
        """ See interfaces.IMailFolder """
        if self.mailbox is None:
            current = self
            while current is not None and not IMailBox.providedBy(current):
                current = aq_inner(aq_parent(current))

            if current is None or not IMailBox.providedBy(current):
                return None
                #raise MailContainerError('object not contained in a mailbox')

            self.mailbox = current
            return current
        else:
            return self.mailbox

    def getMailFolder(self):
        return self.aq_inner.aq_parent

    def _getServerMailList(self):
        """ returns direct server content """
        # need caching and recursion
        server_name = self.server_name
        if server_name == '':
            return []
        connector = self._getconnector()
        uids = connector.search(server_name, None, 'ALL')
        # getting folders
        server_directory = connector.list()
        folders = []
        depth = len(server_name.split('.'))
        for directory in server_directory:
            dir_split = directory['Name'].split('.')
            dir_depth = len(dir_split)
            if dir_depth == depth + 1:
                if directory['Name'].startswith(server_name):
                    folders.append(dir_split[-1])
        return folders + [self.getIdFromUid(uid) for uid in uids]

    def getMailMessages(self, list_folder=True, list_messages=True,
                        recursive=False):
        """See interfaces.IMailFolder

        >>> from mailbox import MailBox
        >>> mb = MailBox()
        >>> f = mb._addFolder('folder', 'folder')
        >>> f.getMailMessages()
        []
        """
        results = []
        if list_folder:
            # use btree slices
            r1 = self.getValuesSlice(' ', '-\xff') # '-' is before '.'
            r2 = self.getValuesSlice('/', '\xff') # '/' is after '.'
            folders = list(r1) + list(r2)
            results.extend(folders)

        if list_messages:
            # use btree slices
            # catalogs starts with a '.z' and are neither msg nor folder
            r = self.getValuesSlice('.', '.y')
            results.extend(list(r))

        if recursive:
            if not list_folder:
                r1 = self.getValuesSlice(' ', '-\xff') # '-' is before '.'
                r2 = self.getValuesSlice('/', '\xff') # '/' is after '.'
                folders = list(r1) + list(r2)

            for folder in folders:
                subresults = folder.getMailMessages(list_folder,
                                                    list_messages,
                                                    recursive)
                results.extend(subresults)

        return results


    def getMailMessagesCount(self, count_folder=True,
                             count_messages=True, recursive=False):
        """ See interfaces.IMailFolder
        >>> from mailbox import MailBox
        >>> mb = MailBox()
        >>> f = mb._addFolder('folder', 'folder')
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

    def _loweritem(self, item):
        return item.lower()

    def getFlaggedMessageCount(self, flags=[]):
        """ returns a number of msg """
        key = '<<>>'.join(flags)
        count = self._cache.query(key)
        if count is not None:
            return count
        else:
            count = len(self.getFlaggedMessageList(flags))
            self._cache.set(count, key)
            return count

    def getFlaggedMessageList(self, flags=[]):
        """ returns a list according to given flags """
        flags = map(self._loweritem, flags)

        msgs = self.getMailMessages(list_folder=False,
            list_messages=True, recursive=False)

        msg_list = []

        # opti : 'seen' is the most common call
        if len(flags) == 1 and flags[0] == 'unseen':
            for msg in msgs:
                if msg.seen == 0:
                    msg_list.append(msg)
            return msg_list

        for msg in msgs:
            cond1 = 'seen' in flags and msg.seen
            cond2 = 'answered' in flags and msg.answered
            cond3 = 'deleted' in flags and msg.deleted
            cond4 = 'flagged' in flags and msg.flagged
            cond5 = 'forwarded' in flags and msg.forwarded
            cond6 = 'unseen' in flags and not msg.seen
            if cond1 and cond2 and cond3 and cond4 and cond5 and cond6:
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
        """ moves the message to another mailbox """
        self._clearCache()
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
        to_mailbox._clearCache()
        msg = getattr(to_mailbox, id)
        self._indexMessage(msg)
        return msg

    def _copyMessage(self, uid, to_mailbox):
        """ copies a message """
        id = self.getIdFromUid(uid)
        msg = self[id]
        new_uid = to_mailbox.getNextMessageUid()
        msg_copy = to_mailbox._addMessage(new_uid, msg.digest)
        msg_copy.copyFrom(msg)

    def _deleteMessage(self, uid):
        """ see interfaces ImailFolder """
        self._clearCache()
        self.clearMailBoxTreeViewCache()
        id = self.getIdFromUid(uid)
        if hasattr(self, id):
            msg = self[id]
            self._unIndexMessage(msg)
            self.manage_delObjects([id])
            self.message_count -=1
            #msg = msg.__of__(None)
            return True
        return False

    def _asyncOnFlagChanged(self, server_name, uid, kw, connector):
        """ asynced """
        try:
            connector.setFlags(server_name, uid, kw)
        except ConnectionError:
            pass

    def onFlagChanged(self, msg, flag, value):
        """ event triggered when a message flag changes """
        # has to be desynced......
        if has_connection:
            connector = self._getconnector()
            flag = flag.capitalize()
            kw = {flag: value}
            connector.setFlags(self.server_name,
                             msg.uid, kw)

        # invalidate cache
        self._clearCache()

    def _addMessage(self, uid, digest, index=True):
        """ See interfaces.IMailFolder """
        self._clearCache()
        self.clearMailBoxTreeViewCache()
        self.message_count +=1
        id = self.getIdFromUid(uid)
        msg = MailMessage(id, uid, digest)
        self._setObject(id, msg)
        msg.parent_folder = self
        msg = self._getOb(id)
        if index:
            # index message into catalog
            self._indexMessage(msg)
        return msg

    def _indexMessage(self, msg):
        """ indexes message """
        mailbox = self.getMailBox()
        mailbox.indexMessage(msg)

    def _unIndexMessage(self, msg):
        """ indexes message """
        mailbox = self.getMailBox()
        mailbox.unIndexMessage(msg)

    def _addFolder(self, uid='', server_name='', server=False):
        """see interfaces.IMailFolder """
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

        if server and has_connection:
            connector = self._getconnector()
            # todo : look at the result
            connector.create(new_folder.server_name)

        return new_folder

    def findMessageByUid(self, uid):
        """ See interfaces.IMailFolder """
        id = self.getIdFromUid(uid)
        try:
            msg = self[id]
        except KeyError:
            return None
        return msg

    def childFoldersCount(self):
        """ See interfaces.IMailFolder """
        return self.getMailMessagesCount(count_folder=True, count_messages=False, \
            recursive=False)

    def getchildFolders(self):
        """ See interfaces.IMailFolder """
        return self.getMailMessages(list_folder=True, list_messages=False)

    def setSyncState(self, state=False, recursive=False):
        """ sets state """
        self.sync_state = state
        if recursive:
            folders = self.getchildFolders()
            for folder in folders:
                folder.setSyncState(state, True)

    def _createKey(self, header):
        """ creates unique key for messages identification """
        s = ''.join(header.values())
        return md5Hash(s)

    def getMessagePart(self, uid, part):
        """ retrieves a part from the server """
        server_name = self.server_name
        connector = self._getconnector()
        fetched = connector.fetch(server_name, uid, '(BODY.PEEK[%s])' % str(part))
        return fetched

    def _loadMessageStructureFromServer(self, server_name, uid, msg_flags,
                                        msg_headers, msg_size, msg_object,
                                        connector, afterload=False):
        """ loads a message from server

        XXX might be outsourced into imap
        """
        if self.instant_load and not afterload:
            msg_object.loadMessage(msg_flags, msg_headers, 'instant_load',
                                   None)
            msg_object.size = msg_size
            msg_object.instant_load = self.instant_load
            return False

        msg_body = None
        skip = False
        part_num = 1
        structure = connector.getMessageStructure(server_name, uid)
        if len(structure) == 1:
            structure = structure[0]

        part_infos =  structure

        if part_infos[0] in ('related', 'relative', 'mixed', 'alternative',
                             'signed'):
            # we don't want to load attached files
            # we just want to get their names
            if part_infos[0] == 'mixed':
                file_list = msg_object.getFileList()
                i = 1
                for part in part_infos[1:]:
                    if isinstance(part, list):
                        have_file = False
                        for sub_part in part:
                            if isinstance(sub_part, list):
                                if sub_part[0] == 'name':
                                    have_file = True
                                    break
                        if have_file:
                            file = {}
                            file['mimetype'] = '%s/%s' % (part[0],
                                                          part[1])
                            file['content-transfer-encoding'] = part[4]
                            file['size'] = part[5]
                            # we don't want to load the file
                            file['data'] = None
                            file['part'] = i
                            for sub in part:
                                if isinstance(sub, list):
                                    if sub[0] == 'name':
                                        file['filename'] = sub[1]
                                        break
                            file_list.append(file)
                        i += 1
            if part_infos[0] in ('mixed', 'related', 'signed'):
                part_infos = part_infos[1]
                part_num = '1'
            else:
                if len(part_infos) > 2:
                    part_infos = part_infos[2]
                    part_num = '2'
                else:
                    # some spams does not give the second part
                    part_infos = part_infos[1]
                    part_num = '1'

        if part_infos[0] == 'alternative':
            if len(part_infos) > 2:
                part_infos = part_infos[2]
                part_num = '%s.2' % part_num
            else:
                part_infos = part_infos[1]
                part_num = '%s.1' % part_num

        elif part_infos[0] == 'relative':
            part_infos = part_infos[1]
            part_num = '%s.1' % part_num
        else:
            part_num = str(part_num)

        try:
            msg_body = connector.fetch(server_name, uid,
                                       '(BODY.PEEK[%s])' % part_num)
        except ConnectionError:
            skip = True

        if not skip:
            msg_object.loadMessage(msg_flags, msg_headers, msg_body,
                                   part_infos)
            msg_object.size = msg_size
            msg_object.instant_load = self.instant_load

        return skip

    def _synchronizeFolder(self, return_log=False, indexStack=[]):
        """ See interfaces.IMailFolder """
        LOG('sync', INFO, 'synchronizing %s' % self.id)
        self._clearCache()
        sync_states = {}
        log = []
        mailbox = self.getMailBox()
        filter_engine = mailbox.getFilters()
        connector = self._getconnector()
        zodb_messages = self.getMailMessages(list_folder=False,
                                             list_messages=True,
                                             recursive=False)
        # now syncing server_folder and current one
        for message in zodb_messages:
            sync_states['%s.%s' % (self.server_name, message.uid)] = False

        try:
            uids = connector.search(self.server_name, None, 'ALL')
        except ConnectionError:
            # XXX should be a more specific exception (no such dir)
            # this will happen if the directory has been
            # deleted form the server
            uids = []


        if self.loose_sync:
            new_list = []
            for part in uids:
                msg = self.findMessageByUid(part)
                if msg is not None:
                    sync_id = '%s.%s' % (self.server_name, part)
                    sync_states[sync_id] = True
                else:
                    new_list.append(part)
            uids = new_list

        # treating n by n
        if len(uids) <= self.fetch_size:
            bloc = [uids]
        else:
            bloc = []
            i = 0
            while i < len(uids):
                if i + self.fetch_size < len(uids):
                    i_end = i +self.fetch_size
                else:
                    i_end = len(uids)

                bloc.append(uids[i:i_end])
                i = i_end

        # XXX will be in properties later
        headers = 'From To Cc Subject Date Message-ID In-Reply-To Content-Type'
        fetch_str = '(FLAGS RFC822.SIZE BODY.PEEK[HEADER.FIELDS(%s)])' % headers
        for sub_bloc in bloc:
            uid_sequence = ','.join(sub_bloc)
            print '%s %s' % (self.id, uid_sequence)
            start = time.time()
            # gets flags, size and headers
            try:

                fetched = connector.fetch(self.server_name, uid_sequence,
                                          fetch_str)
                mailfailed = False
            except ConnectionError:
                fetched = []
                mailfailed = True
            end = time.time() - start
            # now syncing each message
            start_time = time.time()
            i = 0
            y = 0
            if len(sub_bloc) == 1:
                fetched = {sub_bloc[0] : fetched}

            for uid in sub_bloc:
                fetched_mail = fetched[uid]
                sync_id = '%s.%s' % (self.server_name, uid)
                msg = self.findMessageByUid(uid)
                msg_flags = fetched_mail[0]
                msg_size = fetched_mail[1]
                msg_headers = None
                digest = None
                if not mailfailed:
                    msg_headers = fetched_mail[2]
                    subs= ('Date', 'Subject', 'From', 'To', 'Cc', 'Message-ID',
                           'Mailing-List')
                    sub_keys = {}
                    for sub in subs:
                        if msg_headers.has_key(sub):
                            sub_keys[sub] = msg_headers[sub]
                    digest = self._createKey(sub_keys)

                # comparing digest with msg digest
                if msg is not None:
                    if msg.digest != digest:
                        # same uid but not same message
                        old_digest = msg.digest
                        mailbox.addMailToCache(msg, old_digest)
                        # XXX need to remove for catalogs
                        self.manage_delObjects([msg.getId()])
                        msg = None
                    else:
                        sync_states[sync_id] = True
                        continue
                else:
                    msg = mailbox.getMailFromCache(digest, remove=True)

                if msg is None and not mailfailed:
                    msg = self._addMessage(uid, digest, index=False)
                    skip = self._loadMessageStructureFromServer(self.server_name,
                                                                uid, msg_flags,
                                                                msg_headers,
                                                                msg_size, msg,
                                                                connector)

                    if not skip:
                        log.append('adding message %s in %s' % (uid, self.server_name))
                        # XXX todo : load filelist
                        indexStack.append(msg)
                        #self._updateDirectories(msg)

                        # XXX opti might want to call this before
                        # creating the message
                        filter_engine.filterMessage(msg)
                    else:
                        self.manage_delObjects([msg.getId()])
                else:
                    # Message was in cache, adding it to self
                    if not mailfailed:
                        log.append('moving message %s in %s' % (uid,
                                                                self.server_name))
                        self._setObject(msg.getId(), msg)
                    else:
                        log.append('failed to get message %s in %s' \
                                    % (uid, self.server_name))

                sync_states[sync_id] = True
                if msg is not None:
                    self._checkFlags(msg, msg_flags)
                if i > 299:
                    i = 0
                    get_transaction().commit()  # implicitly usable without import
                    get_transaction().begin()   # implicitly usable without import
                    LOG('sync', INFO, '%s %s/%s ' % (self.id,str(y)/str(len(sub_bloc))))
                else:
                    i += 1

                y += 1
            get_transaction().commit()  # implicitly usable without import
            get_transaction().begin()   # implicitly usable without import
            end_time = time.time() - start_time

        # now clear messages in zodb that appears to be
        # deleted from the directory
        # and put them in the cache
        for message in zodb_messages:
            if not sync_states['%s.%s' % (self.server_name, message.uid)]:
                digest = message.digest
                mailbox.addMailToCache(message, digest)
                # XXX need to remove for catalogs
                self.manage_delObjects([message.getId()])
        # used to prevent swapping
        get_transaction().commit()    # implicitly usable without import
        get_transaction().begin()     # implicitly usable without import

        if return_log:
            return log
        else:
            return []

    def _checkFlags(self, msg, flags):
        if flags is not None:
            msg.setFlags(flags)

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

    def rename(self, new_name, fullname=False):
        """ renames the box """
        self._clearCache()
        self.clearMailBoxTreeViewCache()
        oldmailbox = self.server_name

        if not fullname:
            # making sure the new name has no dot
            new_name = new_name.replace('.', '_')

            splitted = oldmailbox.split('.')
            splitted[len(splitted)-1] = new_name
            newmailbox = '.'.join(splitted)
        else:
            newmailbox = new_name

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
        self.mailbox = None
        return self

    def delete(self):
        """ sends the mailbox to the thrash
            by renaming it
        """
        self._clearCache()
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
        self.mailbox = None
        return self.rename(newmailbox, fullname=True)

    def simpleFolderName(self, server_name=''):
        """ retrieves the simple folder name """
        if server_name == '':
            fullname = self.server_name
        else:
            fullname = server_name
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
        if has_connection:
            connector = self._getconnector()
            res = connector.copy(self.server_name, new_mailbox.server_name,
                                 uid)
            connector.setFlags(self.server_name, uid, {'Deleted': 1})
            mailbox.validateChanges()
            if not res:
                return False
        # XXX todo : check if is the same msg uid
        return self._moveMessage(uid, new_mailbox) is not None

    def copyMessage(self, uid, to_mailbox):
        """ make a copy """
        if has_connection:
            connector = self._getconnector()
            res = connector.copy(self.server_name, to_mailbox.server_name, uid)
            if not res:
                return False
        # XXX todo : check if is the same msg uid
        return self._copyMessage(uid, to_mailbox) is not None

    def deleteMessage(self, uid):
        """ moves the message on the server,
            then on the zodb (no sync)
        """
        mailbox = self.getMailBox()

        trash_name = mailbox.getTrashFolderName()
        if has_connection:
            connector = self._getconnector()
            res = connector.copy(self.server_name, trash_name, uid)
            connector.setFlags(self.server_name, uid, {'Deleted': 1})
            if not res:
                return False
        # XXX todo : check if is the same msg uid
        trash = mailbox.getTrashFolder()
        msg = self._moveMessage(uid, trash)
        if msg:
            msg.deleted = 1
            return True
        else:
            return False

    def _updateDirectories(self, message):
        """ update a directory given a message """
        mailbox = self.getMailBox()
        froms = message.getHeader('From')
        for from_ in froms:
            mailbox.addMailDirectoryEntry(from_)

    def depth(self):
        """ calculate the depth """
        server_name = self.server_name
        items = server_name.split('.')
        return len(items)

    def canCreateSubFolder(self):
        """ tells if a sub folder can be created, given a max depth """
        mailbox = self.getMailBox()
        max_depth = mailbox.getConnectionParams()['max_folder_depth']

        if max_depth == 0:
            return True

        current_depth = self.depth()
        return current_depth + 1 <=  max_depth

    def addMailListToCache(self, elements, page, nb_items, sort_with,
                           sort_asc):
        """ to be extern. in mailfolder """
        if not hasattr(self, '_cache'):
            self._cache = RAMCache()

        page_id = '%d.%d.%s.%d' % (page, nb_items, sort_with, sort_asc)
        self._cache.set(elements, page_id)
        self._cache.set((page, nb_items, sort_with, sort_asc), 'last_sort')

    def getMailListFromCache(self, page, nb_items, sort_with, sort_asc):
        """ to be extern. in mailfolder """
        if not hasattr(self, '_cache'):
            self._cache = RAMCache()
            return None

        page_id = '%d.%d.%s.%d' % (page, nb_items, sort_with, sort_asc)
        elements = self._cache.query(page_id)
        return elements

    def getLastMailListSortCache(self):
        """ returns the last sorting parameters """
        return self._cache.query('last_sort')

    def _clearCache(self):
        """ clear the cache """
        self._cache = RAMCache()

    def runFilters(self):
        """ runs filter on folder """
        mailbox = self.getMailBox()
        filter_engine = mailbox.getFilters()
        msgs = self.getMailMessages(list_folder=False, list_messages=True,
                                    recursive=False)
        for msg in msgs:
            filter_engine.filterMessage(msg)

        # XXx opti : to be run only if something has changed
        self._clearCache()


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
