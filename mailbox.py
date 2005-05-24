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
import re
import time
from email.Utils import parseaddr

from zLOG import LOG, DEBUG, INFO
from Globals import InitializeClass
from OFS.Folder import Folder
from OFS.ObjectManager import BadRequest
from ZODB.PersistentMapping import PersistentMapping

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Five import BrowserView
from Products.Five.traversable import FiveTraversable

from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from zope.publisher.browser import FileUpload
from zope.app.cache.ram import RAMCache

from utils import getToolByName, getCurrentDateStr, \
    decodeHeader, uniqueId, makeId, getFolder
from interfaces import IMailBox, IMailMessage, IMailFolder, IMessageTraverser
from mailfolder import MailFolder, manage_addMailFolder
from maileditormessage import MailEditorMessage
from mailfolderview import MailFolderView
from baseconnection import ConnectionError, BAD_LOGIN, NO_CONNECTOR
from basemailview import BaseMailMessageView
from mailmessageview import MailMessageView
from mailsearch import MailCatalog, ZemanticMailCatalog
from directorypicker import DirectoryPicker
from baseconnection import has_connection
from mailfiltering import ZMailFiltering


class MailFolderTicking(MailFolder):

    _idle_time = 30

    def __init__(self, uid, server_name, **kw):
        MailFolder.__init__(self, uid, server_name, **kw)
        self._tick = PersistentMapping()
        self._tick['time'] = self._idle_time + 1

    def isSynchronizing(self):
        """ check if the mailbox is synchronizing

        if the last tick is younger than 30 seconds,
        we are synchronizing
        """
        return time.time() - self._tick['time'] < self._idle_time

    def synchroTick(self):
        """ ticking """
        self._tick['time'] = time.time()

    def clearSynchro(self):
        """ ticking """
        self._tick['time'] = self._idle_time + 1

class MailBoxBaseCaching(MailFolderTicking):
    """ a mailfolder that implements
        mail box caches
    """
    def __init__(self, uid, server_name, **kw):
        MailFolderTicking.__init__(self, uid, server_name, **kw)
        self._cache = RAMCache()

    def addMailToCache(self, msg, key):
        key = {'digest' : key}
        self._cache.set(msg, 'mails', key)

    def getMailFromCache(self, key, remove=True):
        key = {'digest' : key}
        mail = self._cache.query('mails', key)
        if mail is not None and remove:
            self._cache.invalidate('mails', key)
        return mail

    def clearMailCache(self, key=None):
        if key is not None:
            key = {'digest' : key}
        self._cache.invalidate('mails', key)

    def setTreeViewCache(self, treeview):
        self._cache.set(treeview, 'treeview')

    def getTreeViewCache(self):
        return self._cache.query('treeview')

    def clearTreeViewCache(self):
        self._cache.invalidate('treeview')

    def getCurrentEditorMessage(self):
        """ returns the message that is beeing edited
        """
        editor = self._cache.query('maileditor')
        if editor is None:
            msg = MailEditorMessage()
            # hack to identify it , need to do this better
            msg.editor_msg = 1
            msg.setHeader('Date', getCurrentDateStr())
            msg.seen = 1
            self._cache.set(msg, 'maileditor')
            editor = msg
        return editor

    def setCurrentEditorMessage(self, msg):
        """ sets the message that is beeing edited
        """
        # this is done to adapt any kind of message
        editor_msg = self.getCurrentEditorMessage()        # creates it if empty
        editor_msg.loadFromMessage(msg)
        self._cache.set(editor_msg, 'maileditor')

    def clearEditorMessage(self):
        """ empty the cached message
        """
        self._cache.invalidate('maileditor')

    #
    # message clipboard apis
    #
    def fillClipboard(self, action, msg_ids):
        """ adds msgs to clipboard
        """
        self._cache.set(action, 'clipboard_action')
        self._cache.set(msg_ids, 'clipboard_content')

    def getClipboard(self):
        """ get the clipboard content
        """
        action = self._cache.query('clipboard_action')
        msg_ids = self._cache.query('clipboard_content')
        return action, msg_ids

    def clearClipboard(self):
        """ clears clipboard
        """
        self._cache.invalidate('clipboard_action')
        self._cache.invalidate('clipboard_content')

    def clipBoardEmpty(self):
        """ tells if clipboard is empty """
        return self._cache.query('clipboard_content') is None

class MailBox(MailBoxBaseCaching):
    """ the main container

    >>> f = MailBox()
    >>> IMailFolder.providedBy(f)
    True
    >>> IMailBox.providedBy(f)
    True
    """
    ### XXX see if "properties" are ok in zope3/five context
    meta_type = "CPSMailAccess Box"
    portal_type = meta_type

    implements(IMailBox)

    zcatalog_id = '.zemantic_catalog'
    catalog_id = '.zcatalog'

    def __init__(self, uid=None, server_name='', **kw):
        MailBoxBaseCaching.__init__(self, uid, server_name, **kw)
        self.search_available = True
        self._filters = ZMailFiltering()
        self._directory_picker = None
        self._connection_params = PersistentMapping()

    def getConnectionParams(self):
        if self._connection_params == {}:
            portal_webmail = getToolByName(self, 'portal_webmail')
            self._connection_params = portal_webmail.default_connection_params
        if not self._connection_params.has_key('uid'):
            uid = self.id.replace('box_', '')
            self._connection_params['uid'] = uid
        return self._connection_params

    def getFilters(self):
        return self._filters

    def hasFilters(self):
        return self._filters.getFilterCount() > 0

    def _getDirectoryPicker(self):
        if self._directory_picker is None:
            # the one and  only one link to portal_directories
            portal_directories = getToolByName(self, 'portal_directories')
            self._directory_picker = DirectoryPicker(portal_directories)
        return self._directory_picker

    def setParameters(self, connection_params=None, resync=True):
        """ sets the parameters """
        for key in connection_params.keys():
            self._connection_params[key] = connection_params[key]

        if resync is True:
            self._getconnector()
            self.synchronize()

    def synchronize(self, no_log=False, light=1):
        """ see interface """
        if not has_connection:
            return []
        if self.isSynchronizing():
            return []
        self.synchroTick()
        start_time = time.time()
        indexStack = []
        # retrieving folder list from server
        LOG('synchronize', INFO, 'synchro started light = %s' % str(light))
        connector = self._getconnector()

        if light == 1:
            server_directory = [{'Name': 'INBOX'}]
        else:
            server_directory = connector.list()

        if no_log:
            returned = self._syncdirs(server_directories=server_directory,
                                      return_log=False, indexStack=indexStack,
                                      light=light)
        else:
            log = self._syncdirs(server_directories=server_directory,
                                 return_log=True, indexStack=indexStack,
                                 light=light)

            log.insert(0, 'synchronizing mailbox...')
            log.append('... done')
            logtext = '\n'.join(log)
            returned = logtext

        # run filters on INBOX
        for directory in server_directory:
            dir_ = getFolder(self, directory['Name'])
            dir_.runFilters()

        # now indexing
        LOG('synchro', INFO, 'half time : %s seconds' % \
            (time.time() - start_time))

        # now indexing
        get_transaction().commit()
        get_transaction().begin()
        self.search_available = False
        i = 0
        y = 0
        len_ = len(indexStack)
        for item in indexStack:
            LOG('synchro', INFO, 'indexing %d/%d' %(y, len_))
            self.indexMessage(item)
            if i == 299:
                get_transaction().commit(1)     # used to prevent swapping
                i = 0
            else:
                i += 1
            y += 1
        self.search_available = True
        endtime = time.time() - start_time
        LOG('synchro', INFO, 'total time : %s seconds' % endtime)
        self.clearSynchro()
        return returned

    def _syncdirs(self, server_directories=[], return_log=False,
                  indexStack=[], light=0):
        """ syncing dirs """
        log = []
        self.setSyncState(state=False, recursive=True)
        for directory in server_directories:
            # servers directory are delimited by dots
            dirname = directory['Name']
            #dirattr = directory['Attributes']
            dir_fullpath = dirname.split('.')
            current_dir = self
            size = len(dir_fullpath)
            current = 1
            relative_name = ''

            for part in dir_fullpath :
                if relative_name == '':
                    relative_name = part
                else:
                    relative_name = relative_name + '.' + part
                # if path does not exists
                # let's create it
                # server_name is the key, not Id
                # since folder can hav any caracters
                founded = None
                for id, item in current_dir.objectItems():
                    if item.server_name == relative_name:
                        founded = item
                        break

                if founded is None:
                    part_id = makeId(part)
                    part_id = uniqueId(current_dir, part_id)
                    manage_addMailFolder(current_dir, part_id, relative_name)
                    founded = getattr(current_dir, part_id)

                current_dir.setSyncState(state=True)

                current_dir = founded

                if current == size:
                    current_dir.setSyncState(state=True)
                else:
                    current +=1

        self.setSyncState(state=True)

        # cheking for orphan folders
        if light == 0:
            folders = self.getMailMessages(list_folder=True,
                                           list_messages=False, recursive=True)
        else:
            folders = []

        # let's order folder : leaves at first
        # removing orphan folders
        if light == 0:
            for folder in folders:
                if not folder.sync_state:
                    # before deleting message that this folder hold,
                    # we want to put them in orphan list
                    for id, item in folder.objectItems():
                        if IMailMessage.providedBy(item):
                            digest = item.digest
                            self.addMailToCache(item, digest)

                    # delete the folder (see for order problem later here)
                    parent_folder = folder.aq_inner.aq_parent
                    parent_folder.manage_delObjects([folder.getId()])

        # now syncronizing messages
        # this is done after to be able
        # to retrieve orphan message thus accelerate the work
        if light == 0:
            folders = self.getMailMessages(list_folder=True,
                                           list_messages=False, recursive=True)
        else:
            folders = self.getMailMessages(list_folder=True,
                                           list_messages=False, recursive=False)

        for folder in folders:
            # let's synchronize messages now
            if return_log:
                flog = folder._synchronizeFolder(True, indexStack)
                log.extend(flog)
            else:
                folder._synchronizeFolder(False, indexStack)
            folder.setSyncState(state=False)

        # if there's still elements in mail_cache,
        # that means that the messages are really gone
        self.clearMailCache()

        if return_log:
            return log
        else:
            return []

    def _getconnector(self):
        """get mail server connector
        """
        wm_tool = getToolByName(self, 'portal_webmail')
        if wm_tool is None:
            raise ValueError('portal_webmail is missing')

        # safe scan in case of first call
        if wm_tool.listConnectionTypes() == []:
            wm_tool.reloadPlugins()

        connection_params = self.getConnectionParams()

        # wraps connection params with uid
        # and make translations
        connection_params = self.wrapConnectionParams(connection_params)
        connector = wm_tool.getConnection(connection_params)

        if connector is None:
            raise ValueError(NO_CONNECTOR)
        return connector

    def _sendMailMessage(self, msg_from, msg_to, msg):
        """ sends an instance of MailMessage """
        params = self.getConnectionParams()
        portal_webmail = getToolByName(self, 'portal_webmail')
        maildeliverer = portal_webmail.maildeliverer

        signature = params['signature']
        if signature.strip() != '':
            msg_body = msg.getDirectBody()
            # thunderbird-style signature
            msg_body = msg_body + '\r\n\r\n-- \r\n%s' % signature
            msg.setDirectBody(msg_body)

        msg_content = msg.getRawMessage()

        smtp_host = params['smtp_host']
        smtp_port = params['smtp_port']

        return maildeliverer.send(msg_from, msg_to, msg_content,
                                  smtp_host, smtp_port, None, None)

    def sendEditorsMessage(self):
        """ sends the cached message """
        msg = self.getCurrentEditorMessage()
        if msg is None:
            return False
        msg_from = msg.getHeader('From')
        msg_to = msg.getHeader('To')

        result, error = self._sendMailMessage(msg_from, msg_to, msg)
        if result:
            self._givePoints(msg)
            connector = self._getconnector()
            connector.writeMessage('INBOX.Sent', msg.getRawMessage())

            # on the zodb, by synchronizing INBOX.Sent folder
            if hasattr(self, 'INBOX'):
                if hasattr(self.INBOX, 'Sent'):
                    self.INBOX.Sent._synchronizeFolder(return_log=False)
                else:
                    self._syncdirs()
                    self.INBOX._synchronizeFolder(return_log=False)
            else:
                self._syncdirs()
                self._synchronizeFolder(return_log=False)

            self.clearSynchro()
            self.clearEditorMessage()
            return True, ''
        else:
            return False, error


    def getTrashFolderName(self):
        """ returns the trash name """
        return self.getConnectionParams()['trash_folder_name']

    def getTrashFolder(self):
        """ returns the trash name
        """
        trash_name = self.getTrashFolderName()
        trash = getFolder(self, trash_name)
        if trash is None:
            if not hasattr(self, 'INBOX'):
                self._addFolder('INBOX', 'INBOX', server=True)
            inbox = getattr(self, 'INBOX')
            uid = self.simpleFolderName(trash_name)
            trash = inbox._addFolder(uid, trash_name, server=True)
        return trash

    def getDraftFolderName(self):
        """ returns the draft name """

        return self.getConnectionParams()['draft_folder_name']

    def getDraftFolder(self):
        """ returns the draft folder, creates it in case
            it does not exists yet
        """

        draft_name = self.getDraftFolderName()
        draft = getFolder(self, draft_name)
        if draft is None:
            if not hasattr(self, 'INBOX'):
                self._addFolder('INBOX', 'INBOX', server=True)
            inbox = getattr(self, 'INBOX')
            uid = self.simpleFolderName(draft_name)
            draft = inbox._addFolder(uid, draft_name, server=True)
        return draft

    def getSentFolderName(self):
        """ returns the trash name
        """
        return self.getConnectionParams()['sent_folder_name']

    def getSentFolder(self):
        """ returns the trash name
        """
        sent_name = self.getSentFolderName()
        sent = getFolder(self, sent_name)
        if sent is None:
            if not hasattr(self, 'INBOX'):
                self._addFolder('INBOX', 'INBOX', server=True)
            inbox = getattr(self, 'INBOX')
            uid = self.simpleFolderName(sent_name)
            sent = inbox._addFolder(uid, sent_name, server=True)
        return sent

    def _serverEmptyTrashElement(self, element, folders_to_delete):
        """ empty trash element

        If the element is a folder, need to recursively
        delete sub folders
        """
        if not has_connection:
            return

        trash = self.getTrashFolder()
        trash._cache.invalidate(trash.server_name)

        connector = self._getconnector()
        connector.select(trash.server_name)

        if IMailFolder.providedBy(element):
            # recursively calling
            if element not in folders_to_delete:
                folders_to_delete.append(element)
            sub_items = [ob for id, ob in element.objectItems()]
            for sitem in sub_items:
                self._serverEmptyTrashElement(sitem, folders_to_delete)
        else:
            folder = element.getMailFolder()
            connector.setFlags(folder.server_name,
                                element.uid, {'Deleted': 1})

    def emptyTrashFolder(self):
        """ empty the trash """
        trash = self.getTrashFolder()
        trash._clearCache()
        ids = []
        folders = []
        for id, ob in trash.objectItems():
            ids.append(id)
            self._serverEmptyTrashElement(ob, folders)

        # delete folder from server at last
        connector = self._getconnector()

        # sorting, deepest first
        sorter = []
        for folder in folders:
            name = folder.server_name
            folder_deep = len(name.split('.'))
            sorter.append((folder_deep, name))

        sorter.sort()
        sorter.reverse()

        for folder in sorter:
            connector.deleteMailBox(folder[1])

        # low-level deletion
        trash.manage_delObjects(ids)
        trash.message_count = 0
        trash.folder_count = 0

        # calls expunge
        trash.validateChanges()
        self.clearMailBoxTreeViewCache()

    def _getCatalog(self):
        """ returns the catalog """
        uid = self.id
        catalog_id = self.catalog_id

        if hasattr(self, catalog_id):
            return getattr(self, catalog_id)
        else:
            cat = MailCatalog(catalog_id, uid, uid)
            self._setObject(catalog_id, cat)

        return getattr(self, catalog_id)

    def _getZemanticCatalog(self):
        """ returns the catalog """
        zcatalog_id = self.zcatalog_id

        if hasattr(self, zcatalog_id):
            return getattr(self, zcatalog_id)
        else:
            cat = ZemanticMailCatalog()
            #self._setObject(zcatalog_id, cat)
            setattr(self, zcatalog_id, cat)

        return getattr(self, zcatalog_id)

    def clearMailCatalog(self):
        """ clears the catalog """
        zemantic_cat = self._getZemanticCatalog()
        zemantic_cat.clear()

    def reindexMailCatalog(self):
        """ reindex the catalog """
        zemantic_cat = self._getZemanticCatalog()
        zemantic_cat.clear()

        mails = self.getMailMessages(list_folder=False, list_messages=True,
                                     recursive=True)
        len_ = len(mails)
        i = 0
        y = 0

        start_time = time.time()
        for mail in mails:
            #cat.indexMessage(mail)
            LOG('synchro', INFO, 'indexing %d/%d' %(i, len_))
            zemantic_cat.indexMessage(mail)
            if y == 299:
                get_transaction().commit(1)     # used to prevent swapping
                y = 0
            else:
                y += 1
            i += 1
        endtime = time.time() - start_time
        LOG('synchro', INFO, 'total time : %s seconds' % endtime)

    def indexMessage(self, msg):
        """ indexes message """
        #cat = self._getCatalog()
        #cat.indexMessage(msg)
        zemantic_cat = self._getZemanticCatalog()
        zemantic_cat.indexMessage(msg)

    def unIndexMessage(self, msg):
        """ unindexes message """
        #cat = self._getCatalog()
        #cat.unIndexMessage(msg)
        zemantic_cat = self._getZemanticCatalog()
        zemantic_cat.unIndexMessage(msg)

    def saveEditorMessage(self):
        """ makes a copy of editor message into Drafts """
        # TODO: add a TO section
        if has_connection:
            connector = self._getconnector()
            # need to create the message on server side
            new_uid = connector.writeMessage(drafts.server_name, msg_copy.getRawMessage())
        else:
            new_uid = drafts.getNextMessageUid()

        msg = self.getCurrentEditorMessage()
        subjects = msg.getHeader('Subject')
        if subjects != []:
            subject = subjects[0]
            msg.title = decodeHeader(subject)

        drafts = self.getDraftFolder()

        msg_copy = drafts._addMessage(new_uid, msg.digest, index=False)
        msg_copy.copyFrom(msg)
        # todo check flag on server's side
        msg_copy.draft = 1

    def getIdentitites(self):
        """ returns identities """
        # reads in the directory entry
        uid = self.wrapConnectionParams(self.getConnectionParams())['uid']

        results = self.readDirectoryValue(dirname='members',
            id=uid, fields=['email','givenName', 'sn'])

        if results is None:
            return [{'email' : '?', 'fullname' : '?'}]
        else:
            email = results['email']
            givenName = results['givenName']
            sn = results['sn']
            if givenName == '':
                fullname = sn
            else:
                fullname = '%s %s' %(givenName, sn)

            return [{'email' : email, 'fullname' : fullname}]

    #
    # cps directory apis
    #
    # Will get kicked off when aq problem is resolved


    def readDirectoryValue(self, dirname, id, fields):
        """ see interface
        """
        kw = {'id' : id}
        results = self._searchEntries(dirname, return_fields=fields, **kw)
        if len(results) == 1:
            return results[0][1]
        else:
            return None

    def getDirectoryList(self):
        """ see interface """
        portal_directories = getToolByName(self, 'portal_directories')
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().listVisibleDirectories()
        return portal_directories.listVisibleDirectories()

    def _searchEntries(self, directory_name, return_fields=None, **kw):
        """ search for entries """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().searchEntries(directory_name,
        #    return_fields, **kw)
        return dir_.searchEntries(return_fields, **kw)

    def _createEntry(self, directory_name, entry):
        """ search for entries """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().createEntry(directory_name,
        #    entry)
        return dir_.createEntry(entry)

    def _editEntry(self, directory_name, entry):
        """ edit entry"""
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().createEntry(directory_name,
        #    entry)
        return dir_.editEntry(entry)

    def _hasEntry(self, directory_name, id):
        """ search for entries """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().createEntry(directory_name,
        #    entry)
        return dir_.hasEntry(id)

    def _sortDirectorySearchResult(self, entries, field, max_entries=10):
        sorting = []

        for item in entries:
            key = item[1][field]
            if isinstance(key, unicode):
                key = key.encode('ISO8859-15')    # forcing str for sorting
            sorting.append((key, item))

        sorting.sort()
        sorting.reverse()

        if len(sorting) <= max_entries:
            return [item[1] for item in sorting]

        i = 0
        res = []
        while i <= max_entries:    # maybe souhld use reduce
            res.append(sorting[i][1])
            i += 1
        return res

    #
    # apis that deals with directory manipulations
    #

    def searchDirectoryEntries(self, email):
        #
        kw = {'email' : email}
        adressbook = self._searchEntries('addressbook',
                                         ['fullname', 'email', 'id',
                                          'mails_sent'], **kw)

        private_adressbook = self._searchEntries('.addressbook',
                                                  ['fullname', 'email',
                                                   'id', 'mails_sent'], **kw)

        adressbook.extend(private_adressbook)
        adressbook = self._sortDirectorySearchResult(adressbook, 'mails_sent')

        return adressbook


    def getMailDirectoryEntries(self, max_entries=10):
        """ retrieves all entries

        Entries are sorted with mails_sent field
        so the UI can show at first the buddies
        """
        adressbook = self._searchEntries('addressbook',
                                         ['fullname', 'email', 'id',
                                          'mails_sent'])
        adressbook = self._sortDirectorySearchResult(adressbook, 'mails_sent',
                                                     max_entries)
        private_adressbook = self._searchEntries('.addressbook',
                                                  ['fullname', 'email',
                                                   'id', 'mails_sent'])
        private_adressbook = \
            self._sortDirectorySearchResult(private_adressbook,
                                            'mails_sent', max_entries)
        return [adressbook, private_adressbook]

    def _givePoints(self, msg):
        """ gives points to recipients """
        parts = ('To', 'Cc', 'BCc')
        for part in parts:
            elements = msg.getHeader(part)
            for element in elements:
                entry = self._createMailDirectoryEntry(element)
                if entry is not None:
                    id = entry['id']
                    if not self._hasEntry('.addressbook', id ):
                        self._createEntry('.addressbook', entry)
                    else:
                        entries = self._searchEntries('.addressbook',
                                            ['fullname', 'email', 'id',
                                            'mails_sent'],
                                            **{'id' : id })
                        entry = entries[0][1]
                    entry['mails_sent'] += 1
                    self._editEntry('.addressbook', entry)

    def _createMailDirectoryEntry(self, mail):
        """ translate a mail to an entry """
        entry = {}
        parsed = parseaddr(mail)
        fullname = decodeHeader(parsed[0])
        email = parsed[1]
        if re.match(r'^\w*@\w*\.\w{2,4}', email) is None:
            return None
        entry['fullname'] = fullname
        entry['email'] = email
        if fullname != '':
            extracted = fullname.split(' ')
            entry['givenName'] = extracted[0]
            if len(extracted) > 1:
                entry['sn'] = extracted[1]
        entry['id'] = makeId(email)
        entry['mails_sent'] = 0
        return entry

    def addMailDirectoryEntry(self, mail, private=True):
        """ adds an entry to one of the directory """
        entry = self._createMailDirectoryEntry(mail)
        if entry is None:
            return
        if private:
            if not self._hasEntry('.addressbook', entry['id']):
                self._createEntry('.addressbook', entry)
        else:
            if not self._hasEntry('addressbook', entry['id']):
                self._createEntry('addressbook', entry)

    def wrapConnectionParams(self, params):
        """ wraps connection params """
        # now for each parameter, if it has to be
        # picked in a director, let's do it here
        params_values = map(self._directoryToParam, params.values())
        results = zip(params.keys(), params_values)
        render = {}
        for key, value in results:
            render[key] = value
        return render

    def _directoryToParam(self, value):
        """ check if a given parameter has to be taken from a directory """
        id = self.id.replace('box_', '')
        if isinstance(value, str) and value.startswith('${'):
            name = value[2:-1]
            elements = name.split('.')
            directory = elements[0]
            field = elements[1]
            kw = {'id' : id}
            entries = self._searchEntries(directory, [field], **kw)
            if len(entries) > 1:
                raise Exception('Directory returned more than one entry')
            if len(entries) == 0:
                raise Exception('No entry found in %s for %s' % (directory, id))
            fields = entries[0][1]
            if not fields.has_key(field):
                raise Exception("No field '%s' found in %s" % (field, directory))
            return fields[field]
        return value


    def elementIsInTrash(self, element):
        """ tells if the given element is in trash

        Just working on folders at this time
        """
        if IMailFolder.providedBy(element):
            trash_folder = self.getTrashFolder()
            trash_name = trash_folder.server_name
            folder_name = element.server_name
            return folder_name.startswith(trash_name)
        else:
            return False

    def moveElement(self, from_place, to_place):
        """ moves an element

        do not move folder when :
            o the target folder is a subfolder of the folder

        when moving a message or a folder change flags when :
            o it is coming from a special folder (drafts, sent, trash)
            o it is going to a special folder    (drafts, sent, trash)
        """
        # translating first parameter
        if from_place.find('from_folder_') != -1:
            from_place = from_place[12:]
            from_place = from_place.split('.')
            message_to_folder = False
        else:
            from_place = from_place[4:]
            from_place = from_place.split('__')
            folder = from_place[0].split('.')
            message_id = self.getIdFromUid(from_place[1])
            from_place = folder + [message_id]
            message_to_folder = True

        # translating second parameter
        if to_place.find('to_folder_') != -1:
            to_place = to_place[10:]
            to_place = to_place.split('.')
        else:
            to_place = None

        if to_place is None or from_place is None:
            return None

        # translating name to object
        from_object = self
        i = 0
        for element in from_place:
            # make sure we deal with ids
            if i < len(from_place) - 1 or not message_to_folder:
                element = makeId(element)
            from_object = getattr(from_object, element, None)
            if from_object is None:
                raise element + ' not found'
                break
            i += 1

        to_object = self
        if from_object is not None:
            i = 0
            for element in to_place:
                element = makeId(element)
                to_object = getattr(to_object, element, None)
                if to_object is None:
                    raise element + ' not found'
                    break
                i += 1

        if from_object is not None and to_object is not None:
            if message_to_folder:
                # maybe already in ?
                # see if id comp. instead of object comp. is quicker
                from_folder = from_object.getMailFolder()
                if from_folder != to_object:
                    from_folder.moveMessage(from_object.uid, to_object)
                    # now heading to the old folder
                    return from_folder
            else:
                # is folder a parent of target folder ?
                old_parent = from_object.getMailFolder()
                from_id = from_object.server_name
                to_id = to_object.server_name
                if not to_id.startswith(from_id):
                    from_id = from_id.split('.')[-1]
                    new_id = '%s.%s' % (to_id, from_id)
                    from_object.rename(new_id, fullname=True)
                    return old_parent
        return None

    def reconnect(self):
        """ relogs the box """
        connector = self._getconnector()
        connector.relog()

    def clearMailBodies(self):
        """ remove bodies """
        mails = self.getMailMessages(list_folder=False, list_messages=True,
                                     recursive=True)
        for mail in mails:
            mail.instant_load = True
            mail._getStore()._payload = ''
            mail._file_list = []

# Classic Zope 2 interface for class registering
InitializeClass(MailBox)

#
# MailBox Views
#
class MailBoxParametersView(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)


    def _getParameters(self):
        """ returns a list of parameters
        """
        ob = self.context
        return ob.getConnectionParams()

    def getUserName(self):
       """ retrieves user name """
       return self._getParameters()['uid']

    def renderParameters(self):
        """ renders parameters
        """
        params = self._getParameters()
        form = '<dl>'
        for param in params.keys():
            form += '<dt>%s</dt><dd>%s</dd>' %(param, params[param])
        form += '</dl>'
        return form

    def addParameter(self, name):
        """ sets given parameters
        """
        self._getParameters()[name] = ''
        if self.request is not None:
            self.request.response.redirect('configure.html')

    def setParameters(self, params={}):
        """ sets given parameters
        """
        if self.request is not None and hasattr(self.request, 'form'):
            form = self.request.form
            for element in form.keys():
                params[element] = form[element]

        if params.has_key('submit'):
            del params['submit']

        # XXX need to check each parameters
        # to avoid resync if not needed
        self.context.setParameters(params, False)

        if self.request is not None:
            self.request.response.redirect('configure.html')

    def renderParametersForm(self):
        """ returns a form with parameters

        XXXX see for zope 3 schema/widget use here
        """
        if self.request is not None:
            if self.request.has_key('submit'):
                self.setParameters(self.request)

        params = self._getParameters()
        rendered_params = []

        for param in params.keys():
            if param == 'uid':
                continue
            value = params[param]
            rendered_param = {}
            rendered_param['name'] = param
            rendered_param['value'] = value
            if param == 'password' and not params[param].startswith('${'):
                rendered_param['type'] = 'password'
            elif param == 'signature':
                rendered_param['type'] = 'list'
            else:
                rendered_param['type'] = 'text'

            if isinstance(value, int):
                rendered_param['ptype'] = 'int'
            elif isinstance(value, list):
                rendered_param['ptype'] = 'list'
                value = ','.join(value)
            else:
                rendered_param['ptype'] = 'string'

            rendered_params.append(rendered_param)

        rendered_params.sort()
        return rendered_params

    def renderAddParamForm(self):
        """ returns a form with parameters
            XXXX see for zope 3 form use here
        """
        rendered_param = {}
        rendered_param['name'] = 'name'
        rendered_param['value'] = ''
        rendered_param['type'] = 'text'
        return [rendered_param]

    def clearMailCatalog(self):
        """ clear catalog """
        box = self.context
        box.clearMailCatalog()

        if self.request is not None:
            psm = 'Catalog cleared.'
            self.request.response.redirect('configure.html?msm=%s' % psm)

    def reindexMailCatalog(self):
        """ calls the catalog indexation """
        box = self.context
        box.reindexMailCatalog()

        if self.request is not None:
            psm = 'All mails are indexed'
            self.request.response.redirect('configure.html?msm=%s' % psm)

    def reconnect(self):
        """ calls the box relog """
        box = self.context
        box.reconnect()

        if self.request is not None:
            psm = 'cpsma_relogged'
            self.request.response.redirect('configure.html?msm=%s' % psm)

    def clearMailBodies(self):
        """ calls the box clearer """
        box = self.context
        box.clearMailBodies()

        if self.request is not None:
            psm = 'cpsma_cleared'
            self.request.response.redirect('configure.html?msm=%s' % psm)

#
# MailBoxView Views
#
class MailBoxView(MailFolderView):

    def __init__(self, context, request):
        MailFolderView.__init__(self, context, request)

    def renderMailList(self, flags=[]):
        """ returns mails that contains given flags
        """
        if flags == []:
            return MailFolderView.renderMailList(self)
        else:
            # todo (flag view)
            return ''

    def emptyTrash(self):
        """ empty trash folder """
        mailbox = self.context
        mailbox.emptyTrashFolder()
        trash = mailbox.getTrashFolder()
        if self.request is not None:
            psm = 'Trash expunged.'
            self.request.response.redirect(trash.absolute_url()+\
                                           '/view?msm=%s' % psm)

    def synchronize(self, light=1):
        """ synchronizes mailbox """
        # todo : block a new synchronization if it's already
        # XXX inside
        LOG('synchro', INFO, 'start light:%s' % str(light))
        mailbox = self.context

        if not mailbox.isSynchronizing():
            try:
                mailbox.synchronize(no_log=True, light=light)
                psm = 'cpsma_synchronized'
            except ConnectionError:
                psm = 'cpsma_failed_synchro'
        else:
            psm = 'cps_already_synchronizing'

        if self.request is not None:
            if hasattr(mailbox, 'INBOX'):
                container = mailbox.INBOX
            else:
                container = mailbox
            self.request.response.redirect(container.absolute_url()+ \
                '/view?msm=%s' % psm)

    def moveElement(self, from_place, to_place):
        """ moves an element """
        mailbox = self.context
        target = mailbox.moveElement(from_place, to_place)
        if self.request is not None and target is not None:
            self.request.response.redirect(target.absolute_url()+ '/view')

class MailBoxTraversable(FiveTraversable):
    """ use to vizualize the mail parts in the mail editor
    >>> f = MailBoxTraversable(None)
    >>> IMessageTraverser.providedBy(f)
    True
    """
    implements(IMessageTraverser)

    def traverse(self, path='', request=None):
        if type(path) is list:
            path = path[0]
        # if the path starts with a number, we're on the editor message
        # TODO
        if path == 'editorMessage':
            msg = self._subject.getCurrentEditorMessage()
            return msg
        # let the regular traverser do the job
        return FiveTraversable.traverse(self, path, '')

class MailBoxFiltersView(BrowserView):

    def getFilterCount(self):
        mailbox = self.context
        filters = mailbox.getFilters()
        return len(filters.getFilters())

    def _render(self, item):
        render_item = {}

        if item['subject'] == 'From':
            render_item['subject'] = 'Sender'
        else:
            render_item['subject'] = item['subject']

        render_item['action_param'] = item['action_param']
        render_item['value'] = item['value']

        cond = item['condition']

        if cond == 1:
            render_item['condition']  = 'contains'
        elif cond == 2:
            render_item['condition']  = 'does not contains'
        elif cond == 3:
            render_item['condition']  = 'begins with'
        elif cond == 4:
            render_item['condition']  = 'ends with'
        elif cond == 5:
            render_item['condition']  = 'is'
        elif cond == 6:
            render_item['condition']  = 'is not'
        else:
            render_item['condition'] = '? : %s' % str(cond)

        action = item['action']

        if action == 1:
            render_item['action']  = 'move to'
        elif action == 2:
            render_item['action']  = 'copy to'
        elif action == 3:
            render_item['action']  = 'label with'
        elif action == 4:
            render_item['action']  = 'set junk status'
        else:
            render_item['action'] = '? : %s' % str(action)

        return render_item

    def renderFilters(self):
        """ renders filter list

        Replaces values by human readable values
        """
        mailbox = self.context
        filters = mailbox.getFilters().getFilters()
        return map(self._render, filters)

    def removeFilter(self, index):
        """ removes a filter given its index"""
        mailbox = self.context
        filters = mailbox.getFilters()
        filters.deleteFilter(index)

        if self.request is not None:
            self.request.response.redirect('filters.html')

    def addFilter(self, subject, condition, value, action, action_param=None):
        """ adds a filter given its values """
        mailbox = self.context
        filters = mailbox.getFilters()

        # controling input
        if action != 4 and action_param.strip() == '':
            psm = 'Need an action param'
        else:
            filters.addFilter(subject, condition, value, action, action_param)
            psm = None

        if self.request is not None:
            if psm is None:
                self.request.response.redirect('filters.html')
            else:
                self.request.response.redirect(
                    'filters.html?msm=%s' % psm)

    def moveFilter(self, index, direction):
        """ moves a filter given a direction

                0 : up
                1: down
        """
        mailbox = self.context
        filters = mailbox.getFilters()
        filters.moveFilter(index, direction)
        if self.request is not None:
            self.request.response.redirect('filters.html')

manage_addMailBoxForm = PageTemplateFile(
    "www/zmi_addmailbox", globals())

def manage_addMailBox(container, id=None, server_name ='',
        REQUEST=None, **kw):
    """Add a box to a container (self).
    >>> from OFS.Folder import Folder
    >>> f = Folder()
    >>> ob = manage_addMailBox(f, 'mails')
    >>> f.mails.getId()
    'mails'
    """
    container = container.this()
    ob = MailBox(id, server_name, **kw)
    container._setObject(ob.getId(), ob)
    ob = container._getOb(ob.getId())
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')
    else:
        return ob
