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
from zLOG import LOG, DEBUG, INFO
from Globals import InitializeClass
import sys
from smtplib import SMTP
from utils import getToolByName, getCurrentDateStr, \
    _isinstance, decodeHeader, verifyBody
import thread
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from Products.Five import BrowserView
from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from zope.publisher.browser import FileUpload
from utils import uniqueId, makeId, getFolder
from interfaces import IMailBox, IMailMessage, IMailFolder, IMessageTraverser
from mailmessage import MailMessage
from mailfolder import MailFolder, manage_addMailFolder
from mailfolderview import MailFolderView
from baseconnection import ConnectionError, BAD_LOGIN, NO_CONNECTOR
from mailcache import MailCache
from basemailview import BaseMailMessageView
from mailmessageview import MailMessageView
from Products.Five.traversable import FiveTraversable

lock = thread.allocate_lock()
cache = MailCache()

def getCache():
    lock.acquire()
    try:
        return cache
    finally:
        lock.release()

class MailBox(MailFolder):
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
    _v_treeview_cache = None
    _v_current_editor_message = None
    _v_clipboard = []
    _v_clipboard_action =''

    implements(IMailBox)

    # see here for security
    connection_params = {'uid' : '',
                         'connection_type' : '',
                         'HOST' : '',
                         'password' :'',
                         'login' : '',
                         'smtp_host' : 'localhost',
                         'smtp_port' : 25,
                         'trash_folder_name' : 'INBOX.Trash',
                         'draft_folder_name' : 'INBOX.Drafts',
                         'sent_folder_name' : 'INBOX.Sent',
                         'cache_level' :  2}

    # one mail cache by mailbox
    mail_cache = getCache()

    def __init__(self, uid=None, server_name='', **kw):
        MailFolder.__init__(self, uid, server_name, **kw)

    def setParameters(self, connection_params=None, resync=True):
        """ sets the parameters
        """
        self.connection_params = connection_params

        if resync is True:
            self._getconnector()
            self.synchronize()

    def synchronize(self, no_log=False):
        """ see interface
        """
        # retrieving folder list from server
        connector = self._getconnector()
        server_directory = connector.list()

        if no_log:
            self._syncdirs(server_directory)
        else:
            log = self._syncdirs(server_directory, True)
            log.insert(0, 'synchronizing mailbox...')
            log.append('... done')
            logtext = '\n'.join(log)
            return logtext

        # now check messages within this folder
        # XXXX to be done

    def _syncdirs(self, server_directories = [], return_log=False):
        """ syncing dirs
        """
        log = []

        self.setSyncState(state=False, recursive=True)

        for directory in server_directories:
            # servers directory are delimited by dots
            dirname = directory['Name']
            dirattr = directory['Attributes']
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
                        if not self.mail_cache.has_key(digest):
                            self.mail_cache[digest] = item

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

        # if there's stillelements in mail_cache,
        # that means that thse messages are really gone
        cache_size = len(self.mail_cache)
        if cache_size > 0:
            log.append('deleting %d messages' % cache_size)
            self.mail_cache.clear()

        if return_log:
            return log

    def _getconnector(self):
        """get mail server connector
        """
        wm_tool = getToolByName(self, 'portal_webmail')
        if wm_tool is None:
            raise ValueError(MISSING_TOOL)

        # safe scan in case of first call
        if wm_tool.listConnectionTypes() == []:
            wm_tool.reloadPlugins()

        connection_params = self.connection_params
        connector = wm_tool.getConnection(connection_params)
        if connector is None:
            raise ValueError(NO_CONNECTOR)

        return connector

    def setTreeViewCache(self, treeview):
        """ see interface
        """
        self._v_treeview_cache = treeview

    def getTreeViewCache(self):
        """ see interface
        """
        return self._v_treeview_cache

    def clearTreeViewCache(self):
        """ see interface
        """
        if self._v_treeview_cache is not None:
            self._v_treeview_cache = None


    def _sendMailMessage(self, msg_from, msg_to, msg):
        """ sends an instance of MailMessage
        """
        # sends it
        smtp_host = self.connection_params['smtp_host']
        smtp_port = self.connection_params['smtp_port']
        server = SMTP(smtp_host, smtp_port)
        res = server.sendmail(msg_from, msg_to, msg.getRawMessage())
        server.quit()
        if res != {}:
            # TODO: look upon failures here
            pass
        return True

    def sendEditorsMessage(self):
        """ sends the cached message
        """
        msg = self.getCurrentEditorMessage()
        if msg is None:
            return False
        msg_from = msg.getHeader('From')
        msg_to = msg.getHeader('To')
        verifyBody(msg)
        result = self._sendMailMessage(msg_from, msg_to, msg)
        if result:
            connector = self._getconnector()
            res = connector.writeMessage('INBOX.Sent', msg.getRawMessage())
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



    def sendMessage(self, msg_from, msg_to, msg_subject, msg_body):
        """ sends the message
        """
        ob = self.getCurrentEditorMessage()
        ob.setHeader('Subject', msg_subject)
        ob.setHeader('From', msg_from)
        ob.setHeader('Date', getCurrentDateStr())
        if type(msg_to) is list:
            ob.setHeader('To', ", ".join(msg_to))
        else:
            ob.setHeader('To', msg_to)
        #XXX todo : fill body

        # sends it
        self._sendMailMessage(msg_from, msg_to, ob.getRawMessage())

        # if the sent was ok, copy it to the Send folder
        # a) on the server
        connector = self._getconnector()

        res = connector.writeMessage('INBOX.Sent', ob.getRawMessage())

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

    def getTrashFolderName(self):
        """ returns the trash name
        """
        return self.connection_params['trash_folder_name']

    def getTrashFolder(self):
        """ returns the trash name
        """
        trash_name = self.getTrashFolderName()
        return getFolder(self, trash_name)

    def getDraftFolderName(self):
        """ returns the trash name
        """
        return self.connection_params['draft_folder_name']

    def getDraftFolder(self):
        """ returns the trash name
        """
        draft_name = self.getDraftFolderName()
        return getFolder(self, draft_name)

    def getSentFolderName(self):
        """ returns the trash name
        """
        return self.connection_params['sent_folder_name']

    def getSentFolder(self):
        """ returns the trash name
        """
        sent_name = self.getSentFolderName()
        return getFolder(self, sent_name)

    def getCurrentEditorMessage(self):
        """ returns the message that is beeing edited
        """
        if self._v_current_editor_message is None:
            msg = MailMessage()
            # hack to identify it , need to do this better
            msg.editor_msg = 1
            msg.setHeader('Date', getCurrentDateStr())
            self._v_current_editor_message = msg
        return self._v_current_editor_message

    def clearEditorMessage(self):
        """ empty the cached message
        """
        self._v_current_editor_message = None

    def emptyTrash(self):
        """ empty the trash
        """
        # TODO to do this we need first of all to add message flag managment
        # at this this is a local rough deletion
        trash = self.getTrashFolder()
        ids = []
        for id, ob in trash.objectItems():
            ids.append(id)
        trash.manage_delObjects(ids)
        trash.message_count = 0
        trash.folder_count = 0
        connector = self._getconnector()
        connector.select(trash.server_name)
        self.validateChanges()
        self.clearMailBoxTreeViewCache()

    #
    # message clipboard apis
    #
    def fillClipboard(self, action, msg_ids):
        """ adds msgs to clipboard
        """
        self._v_clipboard = msg_ids
        self._v_clipboard_action = action

    def getClipboard(self):
        """ get the clipboard content
        """
        return self._v_clipboard_action, self._v_clipboard

    def clearClipboard(self):
        """ clears clipboard
        """
        self._v_clipboard = []
        self._v_clipboard_action = ''

    def validateChanges(self):
        """ call expunger
        """
        connector = self._getconnector()
        connector.expunge()

    def reindexMailCatalog(self):
        """ reindex the catalog
        """
        mailtool = getToolByName(self, 'portal_webmail')
        if not self.connection_params.has_key('uid'):
            return
        uid = self.connection_params['uid']
        cat = mailtool.mail_catalogs.getCatalog(uid)
        if cat is None:
            mailtool.mail_catalogs.addCatalog(uid)
            cat = mailtool.mail_catalogs.getCatalog(uid)
        mails = self.getMailMessages(list_folder=False,
            list_messages=True, recursive=True)
        for mail in mails:
            cat.indexMessage(mail)

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
        return ob.connection_params

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
        self.context.connection_params[name] = ''
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
            XXXX see for zope 3 form use here
        """
        if self.request is not None:
            if self.request.has_key('submit'):
                self.setParameters(REQUEST)

        params = self._getParameters()
        rendered_params = []

        for param in params:
            rendered_param = {}
            rendered_param['name'] = param
            rendered_param['value'] = params[param]
            if param == 'password':
                rendered_param['type'] = 'password'
            else:
                rendered_param['type'] = 'text'

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
        mailbox = self.context
        mailbox.emptyTrash()
        trash = mailbox.getTrashFolder()
        if self.request is not None:
            self.request.response.redirect(trash.absolute_url()+'/view')

    def synchronize(self):
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
    """
    """
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
    >>> manage_addMailBox(f, 'mails')
    >>> f.mails.getId()
    'mails'
    """
    container = container.this()
    ob = MailBox(id, server_name, **kw)
    container._setObject(ob.getId(), ob)
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')

