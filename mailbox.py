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
from email.Utils import parseaddr, formatdate

from zLOG import LOG, DEBUG, INFO
from Globals import InitializeClass
from OFS.Folder import Folder
from OFS.ObjectManager import BadRequest
from ZODB.PersistentMapping import PersistentMapping
from AccessControl import Unauthorized
from AccessControl.SecurityManagement import newSecurityManager, \
                                             noSecurityManager
from AccessControl.User import User

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Five import BrowserView
from Products.Five.traversable import FiveTraversable

from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from zope.publisher.browser import FileUpload
from zope.app.cache.ram import RAMCache

from utils import getToolByName, decodeHeader, uniqueId, makeId, getFolder,\
                  createDigest, translate
from interfaces import IMailBox, IMailMessage, IMailFolder, IMessageTraverser
from mailfolder import MailFolder, manage_addMailFolder
from maileditormessage import MailEditorMessage
from mailmessage import MailMessage
from mailfolderview import MailFolderView
from baseconnection import ConnectionError, BAD_LOGIN, NO_CONNECTOR
from basemailview import BaseMailMessageView
from mailmessageview import MailMessageView
from mailsearch import ZemanticMailCatalog, get_uri, union
from directorypicker import DirectoryPicker
from baseconnection import has_connection
from mailfiltering import ZMailFiltering

try:
    from Products.zasyncdispatcher import asyncedCall, canAsync
    can_async = True
except ImportError:
    can_async = False


_idle_time = 30
tickers = {}

def getTicker(name, num):
    key = '%s.%d' % (name, num)
    if not tickers.has_key(key):
        tickers[key] = 0
    return tickers[key]

def setTicker(name, num, value):
    tickers['%s.%d' % (name, num)] = value

class MailFolderTicking(MailFolder):
    """ provide a way to protect some synchronization
        to be launched twice.
    """

    def __init__(self, uid, server_name, **kw):
        MailFolder.__init__(self, uid, server_name, **kw)

    #
    # synchro beat
    #
    def isSynchronizing(self, num=0):
        """ check if the mailbox is synchronizing

        if the last tick is younger than 30 seconds,
        we are synchronizing
        """
        getTickLocker(self.id).acquire()
        try:
            ticker = getTicker(self.id, num)
            if ticker == 0:
                return False
            else:
                return time.time() - ticker < _idle_time
        finally:
            getTickLocker(self.id).release()

    def synchroTick(self, num=0):
        """ ticking """
        getTickLocker(self.id).acquire()
        try:
            setTicker(self.id, num, time.time())
        finally:
            getTickLocker(self.id).release()

    def clearSynchro(self, num=0):
        """ ticking """
        getTickLocker(self.id).acquire()
        try:
            setTicker(self.id, num, 0)
        finally:
            getTickLocker(self.id).release()

    #
    # index beat
    #
    def isIndexing(self, num=0):
        """ check if the mailbox is beeing indexed

        if the last tick is younger than 30 seconds,
        we are indexing
        """
        lock_id = self.id + '_index'
        getTickLocker(lock_id).acquire()
        try:
            ticker = getTicker(self.id, num)
            if ticker == 0:
                return False
            else:
                return time.time() - ticker < _idle_time
        finally:
            getTickLocker(lock_id).release()

    def indexTick(self, num=0):
        """ ticking """
        lock_id = self.id + '_index'
        getTickLocker(lock_id).acquire()
        try:
            setTicker(lock_id, num, time.time())
        finally:
            getTickLocker(lock_id).release()

    def clearIndexLocker(self, num=0):
        """ ticking """
        lock_id = self.id + '_index'
        getTickLocker(lock_id).acquire()
        try:
            setTicker(lock_id, num, 0)
        finally:
            getTickLocker(lock_id).release()

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
            msg.setHeader('Date', formatdate())
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
        __version__ = (1, 0, 0, 'b2')
        MailBoxBaseCaching.__init__(self, uid, server_name, **kw)
        self.search_available = True
        self._filters = ZMailFiltering()
        self._directory_picker = None
        self._connection_params = PersistentMapping()

    def _setConnectionValue(self, key, value):
        """ avoids zodb extra writes """
        if self._connection_params.has_key(key):
            if self._connection_params[key] != value:
                self._connection_params[key] = value
        else:
            self._connection_params[key] = value

    def getConnectionParams(self, remove_security=True):
        """ retrieve connection params """
        getLocker(self.id).acquire()
        try:
            portal_webmail = getToolByName(self, 'portal_webmail')
            defaults = portal_webmail.default_connection_params
            if self._connection_params == {}:
                for key in defaults.keys():
                    # -1 are not visible from mailboxes
                    if defaults[key] != -1:
                        self._setConnectionValue(key, defaults[key])
            else:
                # updating
                for key in defaults.keys():
                    value = defaults[key]
                    portalwide = value[1] == 1
                    if portalwide or not self._connection_params.has_key(key):
                        self._setConnectionValue(key, value)
                    elif not portalwide:
                        local_value = self._connection_params[key]
                        if local_value[1] == 1:
                            self._setConnectionValue(key, (local_value[0], 0))

            if not self._connection_params.has_key('uid'):
                uid = self.id.replace('box_', '')
                self._setConnectionValue('uid', (uid, 0))

            params = {}
            if remove_security:
                for key in self._connection_params.keys():
                    params[key] = self._connection_params[key][0]
            else:
                for key in self._connection_params.keys():
                    params[key] = self._connection_params[key]

            return params
        finally:
            getLocker(self.id).release()

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

    def setParameters(self, connection_params=None):
        """ sets the parameters """
        getLocker(self.id).acquire()
        try:
            for key in connection_params.keys():
                self._setConnectionValue(key, connection_params[key])
        finally:
            getLocker(self.id).release()

    def synchronize(self, no_log=False, light=1):
        """ see interface """
        if not has_connection:
            return []
        if self.isSynchronizing(1):
            return []
        self.synchroTick(1)
        start_time = time.time()
        indexStack = []
        # retrieving folder list from server
        LOG('synchronize', DEBUG, 'synchro started light = %s' % str(light))

        # the synchronization is done in a second connector
        # thus leaving the first one available for other manipulations
        connector = self._getconnector(1)

        if light == 1:
            server_directory = [{'Name': 'INBOX'}]
        else:
            server_directory = connector.list()

        if no_log:
            returned = self._syncdirs(server_directories=server_directory,
                                      return_log=False, indexStack=indexStack,
                                      light=light, connection_number=1)
        else:
            log = self._syncdirs(server_directories=server_directory,
                                 return_log=True, indexStack=indexStack,
                                 light=light, connection_number=1)

            log.insert(0, 'synchronizing mailbox...')
            log.append('... done')
            logtext = '\n'.join(log)
            returned = logtext

        # run filters on INBOX
        LOG('synchro', DEBUG, 'running filters')
        for directory in server_directory:
            dir_ = getFolder(self, directory['Name'])
            dir_.runFilters()
        LOG('synchro', DEBUG, 'done running filters')

        # now indexing
        LOG('synchro', DEBUG, 'half time : %s seconds' % \
            (time.time() - start_time))

        # now indexing
        get_transaction().commit()
        get_transaction().begin()
        self.indexMails(indexStack, background=False)
        endtime = time.time() - start_time
        LOG('synchro', DEBUG, 'total time : %s seconds' % endtime)
        self.clearSynchro(1)
        return returned

    def indexMails(self, index_stack, background=False):
        """ indexes mails """
        if self.isIndexing(1):
            return None

        # if backgrounded, tries to put a call
        if background:
            if can_async and canAsync(self):
                portal_url = getToolByName(self, 'portal_url')
                root = portal_url.getPortalPath()
                root = root.replace('/', '.')
                if root[0] == '.':
                    root = root[1:]
                try:
                    asyncedCall(self,
                        'python:home.%s.portal_webmail.%s.indexMails(%s)' \
                                  % (root, self.id, index_stack))
                    fail_async = False
                except AttributeError:
                    fail_async = True
            else:
                fail_async = True
            if fail_async or not(can_async and canAsync(self)):
                self.indexMails(index_stack)

        # indexation
        try:
            i = 0
            y = 0
            len_ = len(index_stack)
            for item in index_stack:
                LOG('synchro', DEBUG, 'indexing %d/%d' %(y, len_))
                self.indexMessage(item)
                if i == 299:
                    get_transaction().commit(1)     # used to prevent swapping
                    i = 0
                else:
                    i += 1
                y += 1
                self.indexTick(1)
        finally:
            self.clearIndexLocker(1)

    def _syncdirs(self, server_directories=[], return_log=False,
                  indexStack=[], light=0, connection_number=0):
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
                flog = folder._synchronizeFolder(True, indexStack,
                                                 connection_number)
                log.extend(flog)
            else:
                folder._synchronizeFolder(False, indexStack, connection_number)
            folder.setSyncState(state=False)

        # if there's still elements in mail_cache,
        # that means that the messages are really gone
        self.clearMailCache()

        if return_log:
            return log
        else:
            return []

    def _getconnector(self, number=0):
        """get mail server connector
        """
        LOG('connector', DEBUG, str(number))
        wm_tool = getToolByName(self, 'portal_webmail')
        if wm_tool is None:
            raise ValueError('portal_webmail is missing')

        # safe scan in case of first call
        if wm_tool.listConnectionTypes() == []:
            wm_tool.reloadPlugins()

        connection_params = self.getConnectionParams()

        # wraps connection params with uid
        # and make translations
        try:
            connection_params = self.wrapConnectionParams(connection_params)
        except Exception, e:
            # bad configuration
            raise ValueError('Bad configuration parameter: %s' % str(e))

        connector = wm_tool.getConnection(connection_params, number)

        if connector is None:
            raise ValueError(NO_CONNECTOR)
        return connector

    def sendNotification(self, recipient, msg):
        """ sends a notification """
        if isinstance(recipient, unicode):
            recipient = recipient.encode('ISO-8859-15')

        id_ = self.getIdentitites()[0]

        if id_['fullname'] != '':
            msg_from = '%s <%s>' % (id_['fullname'], id_['email'])
        else:
            msg_from = id_['email']

        _notification_subject = translate(self, 'cpsm_notify_subject')
        _notification_subject = _notification_subject.encode('ISO-8859-15')
        _notification_template = translate(self, 'cpsm_notify_body')
        _notification_template = _notification_template.encode('ISO-8859-15')

        portal_webmail = getToolByName(self, 'portal_webmail')
        maildeliverer = portal_webmail.getMailDeliverer()
        msg_subject = msg.getHeader('Subject')[0]
        if isinstance(msg_subject, unicode):
            msg_subject = msg_subject.encode('ISO-8859-15')
        msg_body  = _notification_template
        msg_body = msg_body.replace('_ORIGINAL_MAIL_SUBJECT_', msg_subject)
        msg_notif = MailMessage()
        msg_notif.setDirectBody(msg_body)
        msg_notif.setHeader('Subject', _notification_subject)
        msg_notif.setHeader('From', msg_from)
        msg_notif.setHeader('Date', formatdate())
        msg_notif.setHeader('To', recipient)

        msg_content = msg_notif.getRawMessage()

        params = self.getConnectionParams()
        smtp_host = params['smtp_host']
        smtp_port = params['smtp_port']

        result, error = maildeliverer.send(msg_from, recipient, msg_content,
                                           smtp_host, smtp_port, None, None)

        if result:
            sent_folder = self.getSentFolder()
            connector = self._getconnector()


            uid = connector.writeMessage(sent_folder.server_name,
                                         msg_notif.getRawMessage())

            if uid != '':
                connector.setFlags(sent_folder.server_name, uid, {'Seen': 1})

            # on the zodb, by synchronizing INBOX.Sent folder
            sent_folder._synchronizeFolder(return_log=False)

            self.clearEditorMessage()
            return True, 'cpsma_notification_sent'
        else:
            return False, error

    def _sendMailMessage(self, msg_from, msg_to, msg):
        """ sends an instance of MailMessage """
        params = self.getConnectionParams()
        portal_webmail = getToolByName(self, 'portal_webmail')
        maildeliverer = portal_webmail.getMailDeliverer()

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
            return False, 'KO'
        msg_from = msg.getHeader('From')
        msg_to = msg.getHeader('To') + msg.getHeader('Cc') + msg.getHeader('BCc')
        msg.digest = createDigest(msg)

        try:
            result, error = self._sendMailMessage(msg_from, msg_to, msg)
        except ValueError:
            result = False
            error = 'cpsma_could_not_send'

        if result:
            try:
                self._givePoints(msg)
            except Unauthorized:
                # no home directory
                pass

            sent_folder = self.getSentFolder()
            connector = self._getconnector()

            # remove notification header before copying it
            msg.removeHeader('Disposition-Notification-To')

            uid = connector.writeMessage(sent_folder.server_name,
                                         msg.getRawMessage())

            if uid != '':
                connector.setFlags(sent_folder.server_name, uid, {'Seen': 1})

            # on the zodb, by synchronizing INBOX.Sent folder
            try:
                sent_folder._synchronizeFolder(return_log=False)
            finally:
                self.clearSynchro()

            self.clearEditorMessage()
            return True, 'OK'
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
            try:
                connector.setFlags(folder.server_name,
                                   element.uid, {'Deleted': 1})
            except ConnectionError, e:
                # XXX need to understand why we get illegal
                # calls in AUTH state here
                pass

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

        # set selection on trash, to avoid
        # the cursor to be on folder to be deleted
        connector.select(trash.server_name)

        # sorting, deepest first
        sorter = []
        for folder in folders:
            name = folder.server_name
            folder_deep = len(name.split('.'))
            sorter.append((folder_deep, name))

        sorter.sort()
        sorter.reverse()
        for folder in sorter:
            # XXX should read result here
            connector.deleteMailBox(folder[1])

        # low-level deletion
        trash.manage_delObjects(ids)
        trash.message_count = 0
        trash.folder_count = 0

        # calls expunge
        trash.validateChanges()
        self.clearMailBoxTreeViewCache()

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

    def reindexMailCatalog(self, background=False):
        """ reindex the catalog """
        zemantic_cat = self._getZemanticCatalog()
        zemantic_cat.clear()

        mails = self.getMailMessages(list_folder=False, list_messages=True,
                                     recursive=True)

        self.indexMails(mails, background=background)

    def indexMessage(self, msg, index_relations=True):
        """ indexes message """
        zemantic_cat = self._getZemanticCatalog()
        zemantic_cat.indexMessage(msg, index_relations)

    def unIndexMessage(self, msg):
        """ unindexes message """
        zemantic_cat = self._getZemanticCatalog()
        zemantic_cat.unIndexMessage(msg)

    def saveEditorMessage(self):
        """ makes a copy of editor message into Drafts """
        # TODO: add a TO section
        msg = self.getCurrentEditorMessage()
        subjects = msg.getHeader('Subject')
        if subjects != []:
            subject = subjects[0]
            msg.title = decodeHeader(subject)

        msg.draft = 1
        msg.seen = 1
        msg.setHeader('Date', formatdate())

        drafts = self.getDraftFolder()

        # and to server
        if has_connection:
            connector = self._getconnector()

            uid = connector.writeMessage(drafts.server_name, msg.getRawMessage())
            connector.setFlags(drafts.server_name, uid, {'Seen': 1})

            # on the zodb, by synchronizing INBOX.Draft folder
            try:
                drafts._synchronizeFolder(return_log=False)
            finally:
                self.clearSynchro()
        else:
            # copy it to draft folder
            new_uid = drafts.getNextMessageUid()
            msg_copy = drafts._addMessage(new_uid, msg.digest, index=False)
            msg_copy.draft = 1
            msg_copy.seen = 1
            msg_copy.setHeader('Date', formatdate())

    def getIdentitites(self):
        """ returns identities """
        # reads in the directory entry
        uid = self.wrapConnectionParams(self.getConnectionParams())['uid']

        results = self.readDirectoryValue(dirname='members',
            id=uid, fields=['email', 'givenName', 'sn'])

        if results is None:
            email = \
              self.wrapConnectionParams(self.getConnectionParams())['login']
            return [{'email' : email, 'fullname' : ''}]
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

        XXXX need to be in mailtool
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
        """ search for entries

        XXXX need to be in mailtool
        """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().searchEntries(directory_name,
        #    return_fields, **kw)
        results = dir_.searchEntries(return_fields, **kw)
        if results == [] and kw == {'id': '*'}:
            results = dir_.searchEntries(return_fields)
        return results

    def _createEntry(self, directory_name, entry):
        """ search for entries

        XXXX need to be in mailtool
        """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().createEntry(directory_name,
        #    entry)
        return dir_.createEntry(entry)

    def _editEntry(self, directory_name, entry):
        """ edit entry

        XXXX need to be in mailtool
        """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().createEntry(directory_name,
        #    entry)
        return dir_.editEntry(entry)

    def _getDirectoryIdField(self, directory_name):
        """ search for entries

        XXXX need to be in mailtool
        """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        # acquisition pb not resolved yet
        #return self._getDirectoryPicker().getDirectoryIdField(
        # directory_name)
        return dir_.id_field

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
            if item[1].has_key(field):
                key = item[1][field]
            else:
                key = ''
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

    def getPublicAdressBookName(self):
        return self.getConnectionParams()['addressbook']

    def searchDirectoryEntries(self, email):
        """ search directory entries """
        kw = {'email' : email}

        if not '@' in email:
            multiple_search = True
            sub_searches = {'id': email,
                            'givenName': email,
                            'sn': email}
        else:
            multiple_search = False

        addressbook_dir = self.getConnectionParams()['addressbook']
        adressbook = self._searchEntries(addressbook_dir,
                                         ['fullname', 'email', 'id'], **kw)


        if multiple_search:
            for sub_key in sub_searches:
                sub_search = self._searchEntries(addressbook_dir,
                                ['fullname', 'email', 'id'],
                                **{sub_key: sub_searches[sub_key]})

                for entry in sub_search:
                    if entry not in adressbook:
                        adressbook.append(entry)

        try:
            fields = ['fullname', 'email', 'id', 'mails_sent']
            private_adressbook = self._searchEntries('.addressbook', fields,
                                                     **kw)

            if multiple_search:
                for sub_key in sub_searches:
                    sub_search = self._searchEntries('.addressbook', fields,
                                            **{sub_key: sub_searches[sub_key]})

                    for entry in sub_search:
                        if entry not in adressbook:
                            private_adressbook.append(entry)

        except Unauthorized:
            private_adressbook = []

        adressbook.extend(private_adressbook)
        adressbook = self._sortDirectorySearchResult(adressbook, 'mails_sent')

        return adressbook


    def getMailDirectoryEntries(self, max_entries=10):
        """ retrieves all entries

        Entries are sorted with mails_sent field
        so the UI can show at first the buddies
        """
        addressbook_dir = self.getConnectionParams()['addressbook']
        adressbook = self._searchEntries(addressbook_dir,
                                         ['fullname', 'givenName', 'sn',
                                          'email', 'id'],
                                         **{'id': '*'})
        adressbook = self._sortDirectorySearchResult(adressbook, 'mails_sent',
                                                     max_entries)
        # trying to compute fullname
        for entry in adressbook:
            if entry[1]['fullname'].strip() == '':
                givenName = entry[1]['fullname']
                sn = entry[1]['sn']
                id = entry[1]['id']
                entry[1]['fullname'] = ('%s %s' % (givenName, sn)).strip() or id

        try:
            private_adressbook = self._searchEntries('.addressbook',
                                                     ['fullname', 'email',
                                                     'id', 'mails_sent'])
        except Unauthorized:
            private_adressbook = []

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
            directory_identifier = self._getDirectoryIdField(directory)
            kw = {directory_identifier : id}
            entries = self._searchEntries(directory, [field], **kw)
            if len(entries) > 1:
                # trying to figure out the user, if doable
                for entry in entries:
                    if entry[1][directory_identifier] == id:
                        if not entry[1].has_key(field):
                            raise Exception("No field '%s' found in %s" % (field, directory))
                        return entry[1][field]
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

        if to_object.isReadOnly():
            return None

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

    def testConnection(self):
        """ tests the connection """
        try:
            connector = self._getconnector()
            return True, None
        except ConnectionError, e:
            return False, e
        except ValueError, e:
            return False, e

    def searchInConnection(self, query):
        """ sends a query to the connector and mix the results all """
        connector = self._getconnector()
        all_res = []
        # now will make a search into the whole box
        server_directories = connector.list()
        for server_dir in server_directories:
            server_dir = server_dir['Name']
            try:
                dir_res = connector.search(server_dir, None, query)
            except ConnectionError:
                dir_res = []
            if dir_res != [] and dir_res != ['']:
                all_res.append((server_dir, dir_res))

        return all_res

    def getReferences(self, message):
        """ returns refs """
        cat = self._getZemanticCatalog()
        msg_uri = get_uri(message)
        res = cat.make_query((msg_uri, u'replies', None))
        replies = [e.triple()[2] for e in list(res)]

        res = cat.make_query((msg_uri, u'thread', None))
        thread_ = [e.triple()[2] for e in list(res)]
        res = union(replies, thread_)
        bres = self.getBackReferences(message)
        return [element for element in res if element not in bres]

    def getBackReferences(self, message):
        """ returns refs """
        cat = self._getZemanticCatalog()
        msg_uri = get_uri(message)
        res = cat.make_query((msg_uri, u'back-replies', None))
        replies = [e.triple()[2] for e in list(res)]

        res = cat.make_query((msg_uri, u'back-thread', None))
        thread = [e.triple()[2] for e in list(res)]
        return union(replies, thread)

    def isSpecialFolder(self, folder=None):
        """ returns True if folder is None
            (mailbox *is* a specialfolder)
            otherwise checks it in list
        """
        if folder is None:
            return True
        special_folders = (self.getDraftFolderName(),
                           self.getTrashFolderName(), self.getSentFolderName())

        return folder.server_name in special_folders

# Classic Zope 2 interface for class registering
InitializeClass(MailBox)

#
# MailBox Views
#
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
            psm = 'cpsma_expunged'
            self.request.response.redirect(trash.absolute_url()+\
                                           '/view?msm=%s' % psm)

    def synchronize(self, light=1):
        """ synchronizes mailbox """
        # todo : block a new synchronization if it's already
        # XXX inside
        LOG('synchro', DEBUG, 'start light:%s' % str(light))
        mailbox = self.context

        if not mailbox.isSynchronizing(1):
            try:
                mailbox.synchronize(no_log=True, light=light)
                psm = 'cpsma_synchronized'
            except ConnectionError, e:
                psm = str(e)
                mailbox.clearSynchro(1)
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
        psm = 'cpsma_moved'
        if self.request is not None and target is not None:
            self.request.response.redirect(target.absolute_url() + \
                                           '/view?msm=%s' % psm)

    def getunicodetext(self, message):
        """ retrieves a translation in a full unicode response """
        mailbox = self.context
        self.request.response.setHeader('content-type',
                                        'text/plain; charset=utf-8')
        return translate(mailbox, message)

    def background_synchronisation(self, light=1):
        """ background synchronisation """
        mailbox = self.context
        box_name = mailbox.id

        req = self.request
        res = True

        portal_url = getToolByName(self, 'portal_url')

        # looking for zasync
        if can_async and canAsync(self):
            # XXX need to get feedback in case of failures
            bckgrd = True
            root = portal_url.getPortalPath()
            root = root.replace('/', '.')
            if root[0] == '.':
                root = root[1:]
                try:
                    asyncedCall(self,
                        'python:home.%s.portal_webmail.%s.synchronize(light=%s)' \
                          % (root, box_name, str(light)))
                    fail_async = False
                except AttributeError:
                    fail_async = True
        else:
            fail_async = True

        if fail_async or not (can_async and canAsync(self)):
            bckgrd = False

            if not mailbox.isSynchronizing(1):
                try:
                    mailbox.synchronize(no_log=True, light=light)
                    psm = 'cpsma_synchronized'
                    res = True
                except (ConnectionError, ValueError), e:
                    psm = str(e)
                    mailbox.clearSynchro(1)
                    res = False
            else:
                psm = 'cps_already_synchronizing'

        if req is not None:
            root = portal_url()
            if res:
                if bckgrd:
                    psm = 'cps_synchronizing'

            if hasattr(mailbox, 'INBOX'):
                page = '%s/portal_webmail/%s/INBOX' %(root, box_name)
            else:
                page = '%s/portal_webmail/%s' %(root, box_name)

            if psm is not None:
                req.response.redirect('%s/view?msm=%s'  % (page, psm))
            else:
                req.response.redirect('%s/view'  % page)

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

import thread
lockers = {}

def getLocker(name):
    global lockers
    if name not in lockers:
        lockers[name] = thread.allocate_lock()
    return lockers[name]

tick_lockers = {}

def getTickLocker(name):
    global tick_lockers
    if name not in tick_lockers:
        tick_lockers[name] = thread.allocate_lock()
    return tick_lockers[name]


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
