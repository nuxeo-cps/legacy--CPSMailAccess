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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from utils import uniqueId, makeId
from Products.CPSMailAccess.interfaces import IMailBox
from Products.CPSMailAccess.mailfolder import MailFolder, MailFolderView, \
    manage_addMailFolder
from Products.CPSMailAccess.baseconnection import ConnectionError, BAD_LOGIN, \
    NO_CONNECTOR
from Products.CPSMailAccess.mailcache import MailCache
from interfaces import IMailFolder, IMailMessage
from Globals import InitializeClass
from zope.schema.fieldproperty import FieldProperty
from Products.Five import BrowserView

### see for CMF dependency here
#from Products.CMFCore.utils import getToolByName
from utils import getToolByName

import thread

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

    implements(IMailBox)

    # see here for security
    connection_params = {'uid' : '',
                         'connection_type' : '',
                         'HOST' : '',
                         'password' :'',
                         'login' : ''}

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

    def synchronize(self, REQUEST=None):
        """ see interface
        """
        # retrieving folder list from server
        connector = self._getconnector()
        server_directory = connector.list()

        if not REQUEST:
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
                # before deleting message that this folder hold,
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
        self.context[name] = ''
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

#
# MailBoxView Views
#
class MailBoxView(MailFolderView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def renderMailList(self, flags=[]):
        """ returns mails that contains given flags
        """
        if flags == []:
            return MailFolderView.renderMailList(self)
        else:
            return ''

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

