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
from Products.CPSMailAccess.interfaces import IMailBox, IMapping
from Products.CPSMailAccess.mailfolder import MailFolder, manage_addMailFolder
from Products.CPSMailAccess.baseconnection import ConnectionError, BAD_LOGIN, \
    NO_CONNECTOR
from Products.CPSMailAccess.mailcache import MailCache
from interfaces import IMailFolder, IMailMessage
from Globals import InitializeClass
from zope.schema.fieldproperty import FieldProperty

### see for CMF dependency here
from Products.CMFCore.utils import getToolByName

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
    >>> IMapping.providedBy(f)
    True
    """
    ### XXX see if "properties" are ok in zope3/five context
    meta_type = "CPSMailAccess Box"
    portal_type = meta_type

    implements(IMailBox, IMapping)

    # see here for security
    connection_params = FieldProperty(IMailBox['connection_params'])

    # one mail cache by mailbox
    mail_cache = getCache()

    def __init__(self, uid=None, server_name='', **kw):
        MailFolder.__init__(self, uid, server_name, **kw)
        self.connection_params = {}

    def setParameters(self, connection_params, resync=True):
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
                        if not self.mail_cache.inCache(item):
                            self.mail_cache.putMessage(item)

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
            self.mail_cache.emptyList()

        if return_log:
            return log

    def _appendProperties(self, params = {}):
        """ appends properties to param dictionnary
        """
        for property in self._properties:
            id = property['id']
            value = getattr(self, id)
            params[id] = value
        return params

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
        connection_params = self._appendProperties(connection_params)
        connector = wm_tool.getConnection(connection_params)

        if connector is None:
            raise ValueError(NO_CONNECTOR)

        return connector

    #
    # MAPPING INTERFACE for connection params internal dict. (partial)
    #
    # this is used to catch property changes that might
    # need to call some actions
    def __len__(self):
        """ see interface
        """
        return len(self.connection_params)

    def __getitem__(self, name):
        """ see interface
        """
        return self.connection_params[name]

    def __setitem__(self, name, val):
        """ see interface
        """
        found = False
        self.connection_params[name] = val

    def __delitem__(self, name):
        """ see interface
        """
        del self.connection_params[name]

    def has_key(self, name):
        """ see interface
        """
        return self.connection_params.has_key(name)

    def keys(self):
        """ see interface
        """
        return self.connection_params.keys()

    def values(self):
        """ see interface
        """
        return self.connection_params.values()

    def items(self):
        """ see interface
        """
        return self.connection_params.items()


""" classic Zope 2 interface for class registering
"""
InitializeClass(MailBox)

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

