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
import time, thread
from zLOG import LOG, DEBUG, INFO
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner, aq_base
from Products.Five import BrowserView
from ZODB.POSException import ConflictError

from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from zope.app.cache.ram import RAMCache

from mailmessage import MailMessage
from mailexceptions import MailContainerError
from interfaces import IMailFolder, IMailMessage, IMailBox
from utils import uniqueId, makeId, md5Hash, decodeHeader, getFolder,\
                  AsyncCall, createDigestFromList
from baseconnection import has_connection, ConnectionError

folder_locker = {}

def getFolderLocker(mailfolder):
    global folder_locker
    if mailfolder not in folder_locker:
        folder_locker[mailfolder] = thread.allocate_lock()
    return folder_locker[mailfolder]


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
    message_count = 0
    folder_count = 0
    loose_sync = True   # xxx this should be always true now
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
        self._mailbox = None

    def _localGetNextMessageUid(self):
        """ retrieves next id based on local calculation """
        msgs = self.getMailMessages(list_folder=False, list_messages=True,
                                        recursive=False)
        highest_id = 0
        for msg in msgs:
            uid = int(msg.uid)
            if uid > highest_id:
                highest_id = uid
        return str(highest_id + 1)

    def getNextMessageUid(self):
        """ retrieves next id for messages """
        if has_connection == 1:
            connector = self._getconnector()
            return connector.getNextUid(self.server_name)
        else:
            return self._localGetNextMessageUid()


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
        """ See interfaces.IMailFolder

        XXX should be memoized
        """
        current = self
        while current is not None and not IMailBox.providedBy(current):
            current = aq_inner(aq_parent(current))

        if current is None or not IMailBox.providedBy(current):
            return None
        else:
            return current

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
        getFolderLocker(self.server_name).acquire()
        try:
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
        finally:
            getFolderLocker(self.server_name).release()


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
        """ returns a list according to given flags

        if a flag is prefixed by - it will check
        it negation : -seen, seen, -junk, etc
        """
        flags = map(self._loweritem, flags)
        msgs = self.getMailMessages(list_folder=False,
                                    list_messages=True, recursive=False)
        msg_list = []
        for msg in msgs:
            selected = True
            for flag in flags:
                if flag[0] == '-':
                    c_flag = flag[1:]
                    condition = 0
                else:
                    c_flag = flag
                    condition = 1

                if not hasattr(msg, c_flag):
                    selected = False
                    break
                elif getattr(msg, c_flag) != condition:
                    selected = False
                    break

            if selected:
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

    def getUidFromId(self, id):
        """Get the uid out of the zope id """
        if id[0] == '.':
            id = id[1:]
        return id

    def _copyMessage(self, uid, to_mailbox):
        """ copies a message """
        id = self.getIdFromUid(uid)
        if self.has_key(id):
            msg = self[id]
            new_uid = to_mailbox.getNextMessageUid()
            msg_copy = to_mailbox._addMessage(new_uid, msg.digest)
            msg_copy.copyFrom(msg)
            return True
        return False

    def _deleteMessage(self, uid):
        """ deletes a message """
        self._clearCache()
        self.clearMailBoxTreeViewCache()
        id = self.getIdFromUid(uid)

        if self.has_key(id):
            # unindexing before unwrapping
            self._unIndexMessage(self._getOb(id))
            msg = aq_base(self._getOb(id))
            self._delOb(id)
            self.message_count -= 1
            return True

        return False

    def changeMessageFlags(self, msg, flag, value):
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
        if self.has_key(id):
            raise Exception('The id %s is invalid in %s - it\'s in use' \
                %(id, self.id))
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
        index_relations = not mailbox.isSpecialFolder(self)
        mailbox.indexMessage(msg, index_relations=index_relations)

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
            try:
                connector = self._getconnector()
            except ConnectionError:
                pass
            else:
                # todo : look at the result
                connector.create(new_folder.server_name)

        return new_folder

    def findMessageByUid(self, uid):
        """ See interfaces.IMailFolder """
        id = self.getIdFromUid(uid)
        try:
            msg = self[id]
            if IMailMessage.providedBy(msg):
                return msg
            else:
                return None
        except KeyError:
            return None

    def childFoldersCount(self):
        """ See interfaces.IMailFolder """
        return self.getMailMessagesCount(count_folder=True,
                                          count_messages=False,
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

    def getMessagePart(self, uid, part):
        """ retrieves a part from the server """
        server_name = self.server_name
        connector = self._getconnector()
        fetched = connector.fetch(server_name, uid, '(BODY.PEEK[%s])' \
                                                     % str(part))
        return fetched

    def _loadMessageStructureFromServer(self, server_name, uid, msg_flags,
                                        msg_headers, msg_size, msg_object,
                                        connector, afterload=False):
        """ loads a message from server

        XXX might be outsourced into imap and cleaned
        """
        if self.instant_load and not afterload:
            msg_object.loadMessage(msg_flags, msg_headers, 'instant_load',
                                   None)
            msg_object.size = msg_size
            msg_object.instant_load = self.instant_load
            # we need to check if the message has attached files
            # XXX how to do this without loading the structure
            # ie : without making the webmail very slow
            return False

        msg_body = None
        skip = False
        part_num = 1
        structure = connector.getMessageStructure(server_name, uid)
        if len(structure) == 1:
            structure = structure[0]

        part_infos = structure

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
                                if (sub_part[0] == 'name'):
                                    have_file = True
                                    break
                                if (len(sub_part) > 3 and
                                    sub_part[2] == 'name'):
                                    have_file = True
                                    break
                        if have_file:
                            file = {}
                            if part[0] == 'unknown':
                                file['mimetype'] = ''
                            else:
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
                                    if len(sub) > 3 and sub[2] == 'name':
                                        file['filename'] = sub[3]
                                        break
                            file_list.append(file)
                        i += 1
            if part_infos[0] in ('mixed', 'related', 'signed'):
                part_infos = part_infos[1]
                part_num = '1'
                i = 1
                file_list = msg_object.getFileList()
                for part in part_infos[1:]:
                    if isinstance(part, list):
                        have_file = False
                        for sub_part in part:
                            if isinstance(sub_part, list):
                                if (sub_part[0] == 'name'):
                                    have_file = True
                                    break
                                if len(sub_part) > 3 and sub_part[2] == 'name':
                                    have_file = True
                                    break
                        if have_file:
                            file = {}
                            if part[0] == 'unknown':
                                file['mimetype'] = ''
                            else:
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
                                    if len(sub) > 3 and sub[2] == 'name':
                                        file['filename'] = sub[3]
                                        break
                            file_list.append(file)
                        i += 1
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
        elif part_infos[0] in ('relative', 'signed', 'mixed'):
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
            if msg_size is not None:
                msg_object.size = msg_size
            if not afterload:
                msg_object.instant_load = self.instant_load
            else:
                msg_object.instant_load = False

        return skip

    def _createSubBlocs(self, uids, fetch_size):
        """ cutting into blocs """
        if len(uids) <= fetch_size:
            bloc = [uids]
        else:
            bloc = []
            i = 0
            while i < len(uids):
                if i + fetch_size < len(uids):
                    i_end = i + fetch_size
                    bloc.append(uids[i:i_end])
                    i = i_end
                else:
                    bloc.append(uids[i:])
                    break
        return bloc

    def _synchronizeFolder(self, return_log=False, indexStack=[],
                           connection_number=0):
        """ See interfaces.IMailFolder """
        LOG('_synchronizeFolder', DEBUG, self.id)
        self._clearCache()
        sync_states = {}
        log = []
        mailbox = self.getMailBox()
        mailbox.synchroTick(connection_number)
        connector = self._getconnector(connection_number)
        zodb_messages = self.getMailMessages(list_folder=False,
                                             list_messages=True,
                                             recursive=False)
        # now syncing server_folder and current one
        for message in zodb_messages:
            sync_states['%s' % (message.digest)] = False

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
                    sync_id = '%s' % (msg.digest)
                    sync_states[sync_id] = True
                else:
                    new_list.append(part)
            uids = new_list

        # treating n by n
        bloc = self._createSubBlocs(uids, self.fetch_size)

        # XXX will be in properties later
        headers = ['From', 'To', 'Cc', 'Subject', 'Date', 'Message-ID',
                   'In-Reply-To', 'Content-Type', 'References',
                   'Disposition-Notification-To']

        fetch_str = '(FLAGS RFC822.SIZE BODY.PEEK[HEADER.FIELDS(%s)])' \
                     % ' '.join(headers)
        for sub_bloc in bloc:
            uid_sequence = ','.join(sub_bloc)
            #start = time.time()
            # gets flags, size and headers
            LOG('_synchronizeFolder', DEBUG, 'fetching %s' % str(uid_sequence))
            try:
                fetched = connector.fetch(self.server_name, uid_sequence,
                                          fetch_str)
                mailfailed = False
            except ConnectionError:
                fetched = []
                mailfailed = True
            #end = time.time() - start
            # now syncing each message
            # start_time = time.time()
            if len(sub_bloc) == 1:
                fetched = {sub_bloc[0] : fetched}

            for uid in sub_bloc:
                mailbox.synchroTick(connection_number)
                if not fetched.has_key(uid):
                    LOG('_synchronizeFolder', DEBUG,
                               'failed to get message %s in %s' % \
                               (uid, self.server_name))
                    log.append('failed to get message %s in %s' \
                                % (uid, self.server_name))
                    continue

                fetched_mail = fetched[uid]
                found = False
                msg = self.findMessageByUid(uid)
                msg_flags = fetched_mail[0]
                msg_size = fetched_mail[1]
                msg_headers = None
                digest = None
                if not mailfailed:
                    msg_headers = fetched_mail[2]
                    digest = createDigestFromList(msg_headers)

                # comparing digest with msg digest
                if msg is not None:
                    if msg.digest != digest:
                        # same uid but not same message
                        old_digest = msg.digest
                        mailbox.addMailToCache(msg, old_digest)
                        self._deleteMessage(msg.uid)
                        msg = None
                    else:
                        found = True
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
                        LOG('_synchronizeFolder', DEBUG,
                            'adding message %s in %s' % (uid, self.server_name))
                        log.append('adding message %s in %s' % \
                                   (uid, self.server_name))
                        # XXX todo : load filelist
                        indexStack.append(msg)
                        #self._updateDirectories(msg)
                    else:
                        self._deleteMessage(msg.uid)
                        msg = None
                else:
                    # Message was in cache, adding it to self
                    if not found:
                        if not mailfailed:
                            LOG('_synchronizeFolder', DEBUG,
                                'moving message %s in %s' % (uid, self.server_name))

                            log.append('moving message %s in %s' % \
                                    (uid, self.server_name))
                            self._setObject(msg.getId(), msg)
                        else:
                            LOG('_synchronizeFolder', DEBUG,
                               'failed to get message %s in %s' % \
                               (uid, self.server_name))
                            log.append('failed to get message %s in %s' \
                                        % (uid, self.server_name))

                #sync_states[sync_id] = True
                if msg is not None:
                    self._checkFlags(msg, msg_flags)
                    sync_id = '%s' % msg.digest
                    sync_states[sync_id] = True

            # prevent from swapping and
            # let the user see results as they are fetched
            if connection_number > 0:
                try:
                    get_transaction().commit()
                    get_transaction().begin()
                except ConflictError:
                    # if the user is changing box parameters
                    # the synchronize commit will raise
                    # an error so lets pass this commit
                    pass
            LOG('_synchronizeFolder', DEBUG, 'done fetching')
            #end_time = time.time() - start_time

        # now clear messages in zodb that appears to be
        # deleted from the directory
        # and put them in the cache
        LOG('_synchronizeFolder', DEBUG, 'deleting messages')
        for message in zodb_messages:
            if not sync_states['%s' % message.digest]:
                digest = message.digest
                mailbox.addMailToCache(message, digest)
                # XXX need to remove for catalogs
                self._deleteMessage(message.uid)
        LOG('_synchronizeFolder', DEBUG, 'done deleting messages')

        # prevent from swapping and
        # let the user see results as they are fetched
        if connection_number > 0:
            try:
                get_transaction().commit()
                get_transaction().begin()
            except ConflictError:
                # if the user is changing box parameters
                # the synchronize commit will raise
                # an error so lets pass this commit
                pass
        LOG('_synchronizeFolder done for', DEBUG, self.id)
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

    def _getconnector(self, number=0):
        """See interfaces.IMailFolder
        """
        current = self
        while not IMailBox.providedBy(current) and current is not None:
            current = aq_parent(current)

        if current is not None:
            return current._getconnector(number)
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
        parent._delOb(self.id)
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
            node = makeId(node)
            current = current[node]

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

        self = current[self.id]

        # recreating server name
        if fullname==0:
            self.server_name = newmailbox
        else:
            self.server_name = new_name

        self.title = basename
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
        """ copy a mailbox into another one """
        # TODO
        raise NotImplementedError

    def moveMessage(self, uid, new_mailbox):
        """ moves the message on the server,
            then on the zodb (no sync)
        """
        id = self.getIdFromUid(uid)
        msg = self[id]

        # detach message
        self._deleteMessage(uid)

        # get its new id and uid
        new_uid = new_mailbox.getNextMessageUid()

        new_id = new_mailbox.getIdFromUid(new_uid)
        msg = aq_base(msg)
        msg.uid = new_uid
        msg.id = new_id

        # link it to the newmailbox
        new_mailbox._setObject(new_id, msg)
        new_mailbox.message_count += 1
        new_mailbox._clearCache()
        msg = new_mailbox[new_id]
        msg = msg.__of__(new_mailbox)
        self._indexMessage(msg)

        res = msg is not None

        if has_connection:
            try:
                connector = self._getconnector()
                res = connector.copy(self.server_name, new_mailbox.server_name,
                                    uid)
                connector.setFlags(self.server_name, uid, {'Deleted': 1})
            except ConnectionError:
                res = False
            if not res:
                return False

        self.validateChanges()
        new_mailbox.validateChanges()   # this will provide new id
        return res

    def validateChanges(self):
        """ call expunger """
        if has_connection:
            connector = self._getconnector()
            connector.select(self.server_name)
            connector.expunge()

    def copyMessage(self, uid, to_mailbox):
        """ make a copy """
        # cannot copy within the same dir, that's insane
        if to_mailbox == self:
            return False

        if has_connection:
            try:
                connector = self._getconnector()
                res = connector.copy(self.server_name, to_mailbox.server_name, uid)
            except ConnectionError:
                res = False
            if not res:
                return False
        # XXX todo : check if is the same msg uid
        return self._copyMessage(uid, to_mailbox) is not None

    def deleteMessage(self, uid):
        """ moves the message on the server,
            then on the zodb (no sync)
        """
        mailbox = self.getMailBox()
        trash = mailbox.getTrashFolder()
        return self.moveMessage(uid, trash)

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
        """ xxx to be extern. in mailfolderview """
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

    def _nextId(self, id):
        current_number = self.getUidFromId(id)
        next_id = str(int(current_number) + 1)
        return self.getIdFromUid(next_id)


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
