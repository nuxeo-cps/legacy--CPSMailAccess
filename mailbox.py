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
from email.Utils import parseaddr

from zLOG import LOG, DEBUG, INFO
from Globals import InitializeClass
from OFS.Folder import Folder
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
from mailsearch import MailCatalog
from directorypicker import DirectoryPicker
from baseconnection import has_connection

class MailBoxBaseCaching(MailFolder):
    """ a mailfolder that implements
        mail box caches
    """
    def __init__(self, uid, server_name, **kw):
        MailFolder.__init__(self, uid, server_name, **kw)
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

    _directory_picker = None
    _connection_params = {}

    def __init__(self, uid=None, server_name='', **kw):
        MailBoxBaseCaching.__init__(self, uid, server_name, **kw)

    def getConnectionParams(self):
        if self._connection_params == {}:
            portal_webmail = getToolByName(self, 'portal_webmail')
            self._connection_params = portal_webmail.default_connection_params
        return self._connection_params

    def _getDirectoryPicker(self):
        if self._directory_picker is None:
            # the one and  only one link to portal_directories
            portal_directories = getToolByName(self, 'portal_directories')
            self._directory_picker = DirectoryPicker(portal_directories)
        return self._directory_picker

    def setParameters(self, connection_params=None, resync=True):
        """ sets the parameters
        """
        self._connection_params = connection_params

        if resync is True:
            self._getconnector()
            self.synchronize()

    def synchronize(self, no_log=False):
        """ see interface """
        if not has_connection:
            return []
        # retrieving folder list from server
        connector = self._getconnector()
        server_directory = connector.list()

        if no_log:
            return self._syncdirs(server_directory)
        else:
            log = self._syncdirs(server_directory, True)
            log.insert(0, 'synchronizing mailbox...')
            log.append('... done')
            logtext = '\n'.join(log)
            return logtext

    def _syncdirs(self, server_directories = [], return_log=False):
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
        folders = self.getMailMessages(list_folder=True, list_messages=False, recursive=True)

        # let's order folder : leaves at first
        for folder in folders:
            if not folder.sync_state:
                # before deleti_synchronizeFolderng message that this folder hold,
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
        folders = self.getMailMessages(list_folder=True, list_messages=False, recursive=True)

        for folder in folders:
            # let's synchronize messages now
            if return_log:
                flog = folder._synchronizeFolder(True)
                log.extend(flog)
            else:
                folder._synchronizeFolder()
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
        # sends it
        portal_webmail = getToolByName(self, 'portal_webmail')
        maildeliverer = portal_webmail.maildeliverer

        smtp_host = self.getConnectionParams()['smtp_host']
        smtp_port = self.getConnectionParams()['smtp_port']

        return maildeliverer.send(msg_from, msg_to, msg.getRawMessage(), smtp_host,
                           smtp_port, None, None)

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

            # b) on the zodb, by synchronizing INBOX.Sent folder
            if hasattr(self, 'INBOX'):
                if hasattr(self.INBOX, 'Sent'):
                    self.INBOX.Sent._synchronizeFolder(return_log=False)
                else:
                    self._syncdirs()
                    self.INBOX._synchronizeFolder(return_log=False)
            else:
                self._syncdirs()
                self._synchronizeFolder(return_log=False)
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
            inbox = self['INBOX']
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
            inbox = self['INBOX']
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
            inbox = self['INBOX']
            uid = self.simpleFolderName(sent_name)
            sent = inbox._addFolder(uid, sent_name, server=True)
        return sent

    def _serverEmptyTrashElement(self, element):
        """ empty trash element

        If the element is a folder, need to recursively
        delete sub folders
        """
        if not has_connection:
            return

        trash = self.getTrashFolder()
        connector = self._getconnector()
        connector.select(trash.server_name)

        if IMailFolder.providedBy(element):
            # recursively calling
            sub_items = [ob for id, ob in element.objectItems()]
            map(self._serverEmptyTrashElement, sub_items)

            connector.deleteMailBox(element.server_name)
        else:
            folder = element.getMailFolder()
            connector.setFlags(folder.server_name,
                               element.uid, {'Deleted': 1})


    def emptyTrashFolder(self):
        """ empty the trash """
        trash = self.getTrashFolder()
        ids = []
        for id, ob in trash.objectItems():
            ids.append(id)
            self._serverEmptyTrashElement(ob)

        trash.manage_delObjects(ids)
        trash.message_count = 0
        trash.folder_count = 0

        # calls expunge
        self.validateChanges()
        self.clearMailBoxTreeViewCache()

    def validateChanges(self):
        """ call expunger """
        if has_connection:
            connector = self._getconnector()
            connector.expunge()

    def _getCatalog(self):
        """ returns the catalog
        """
        if not self.getConnectionParams().has_key('uid'):
            raise Exception('Need a uid to get the catalog')

        uid = self.getConnectionParams()['uid']

        catalog_id = '.zcatalog'
        if hasattr(self, catalog_id):
            return getattr(self, catalog_id)
        else:
            cat = MailCatalog(catalog_id, uid, uid)
            self._setObject(catalog_id, cat)

        return getattr(self, catalog_id)

    def reindexMailCatalog(self):
        """ reindex the catalog
        """
        cat = self._getCatalog()
        mails = self.getMailMessages(list_folder=False,
            list_messages=True, recursive=True)
        for mail in mails:
            cat.indexMessage(mail)

    def indexMessage(self, msg):
        """ indexes message """
        cat = self._getCatalog()
        cat.indexMessage(msg)

    def unIndexMessage(self, msg):
        """ unindexes message """
        cat = self._getCatalog()
        cat.unIndexMessage(msg)

    def saveEditorMessage(self):
        """ makes a copy of editor message into Drafts """
        # TODO: add a TO section
        msg = self.getCurrentEditorMessage()
        msg.title = decodeHeader(msg.getHeader('Subject')[0])

        drafts = self.getDraftFolder()
        new_uid = drafts.getNextMessageUid()

        msg_copy = drafts._addMessage(new_uid, msg.digest)
        msg_copy.copyFrom(msg)
        # todo check flag on server's side
        msg_copy.draft = 1

        if has_connection:
            connector = self._getconnector()
            # need to create the message on server side
            connector.writeMessage(drafts.server_name, msg_copy.getRawMessage())

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
        return portal_directories.listVisibleDirectories()
        """ acquisition pb not resolved yet
        return self._getDirectoryPicker().listVisibleDirectories()
        """

    def _searchEntries(self, directory_name, return_fields=None, **kw):
        """ search for entries """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        return dir_.searchEntries(return_fields, **kw)

        """ acquisition pb not resolved yet
        return self._getDirectoryPicker().searchEntries(directory_name,
            return_fields, **kw)
        """
    def _createEntry(self, directory_name, entry):
        """ search for entries """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        return dir_.createEntry(entry)

        """ acquisition pb not resolved yet
        return self._getDirectoryPicker().createEntry(directory_name,
            entry)
        """
    def _editEntry(self, directory_name, entry):
        """ edit entry"""
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        return dir_.editEntry(entry)

        """ acquisition pb not resolved yet
        return self._getDirectoryPicker().createEntry(directory_name,
            entry)
        """

    def _hasEntry(self, directory_name, id):
        """ search for entries """
        portal_directories = getToolByName(self, 'portal_directories')
        dir_ = portal_directories[directory_name]
        return dir_.hasEntry(id)

        """ acquisition pb not resolved yet
        return self._getDirectoryPicker().createEntry(directory_name,
            entry)
        """

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
        if not params.has_key('uid'):
            uid = self.id.replace('box_', '')
            params['uid'] = uid

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

        for param in params:
            value = params[param]
            rendered_param = {}
            rendered_param['name'] = param
            rendered_param['value'] = value
            if param == 'password' and not params[param].startswith('${'):
                rendered_param['type'] = 'password'
            else:
                rendered_param['type'] = 'text'

            if isinstance(value, int):
                rendered_param['ptype'] = 'int'
            else:
                rendered_param['ptype'] = 'string'

            rendered_params.append(rendered_param)

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

    def reindexMailCatalog(self):
        """ calls the catalog indexation
        """
        box = self.context
        box.reindexMailCatalog()

        if self.request is not None:
            psm = 'All mails are indexed'
            self.request.response.redirect('configure.html?portal_status_message=%s' % psm)

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
                                           '/view?portal_status_message=%s' % psm)

    def synchronize(self):
        """ synchronizes mailbox """
        mailbox = self.context
        mailbox.synchronize(True)
        if self.request is not None:
            psm = 'synchronized'
            if hasattr(mailbox, 'INBOX'):
                container = mailbox.INBOX
            else:
                container = mailbox
            self.request.response.redirect(container.absolute_url()+ \
                '/view?portal_status_message=%s' % psm)

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

