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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder

from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements

from utils import uniqueId, makeId
from Products.CPSMailAccess.mailmessage import MailMessage
from interfaces import IMailFolder, IMailMessage

class MailFolder(Folder):
    """A container of mail messages and other mail folders.

    A MailFolder implements IMailFolder:

    >>> f = MailFolder()
    >>> IMailFolder.providedBy(f)
    True
    """
    
    implements(IMailFolder)
    
    server_name = FieldProperty(IMailFolder['server_name'])    
    mail_prefix = FieldProperty(IMailFolder['mail_prefix'])
    
    
    def __init__(self, uid=None, server_name='', **kw):
        """
        >>> f = MailFolder('ok', 'Open.INBOX.Stuffs')
        >>> f.getServerName()
        'Open.INBOX.Stuffs'
        """
        Folder.__init__(self, uid)
        self.mail_prefix = 'msg_'
        self.setServerName(server_name)
        
    def getMailMessages(self, list_folder=True, list_messages=True, recursive=False):
        """See interfaces.IMailFolder
        
        >>> f = MailFolder()
        >>> f.getMailMessages()
        []
        """
        providers = ()
        
        result = []
        
        if list_folder:
            providers = providers+ (IMailFolder,)
                
        if list_messages:
            providers = providers+ (IMailMessage,)
            
        for element in self.objectValues():
            for provider in providers :
                if provider.providedBy(element):
                    result.append(provider(element))
                    
            if recursive:
                if IMailFolder.providedBy(element):
                    result.extend(element.getMailMessages(list_folder, 
                        list_messages, recursive))                        
            
        return result
    
    def getMailMessagesCount(self, count_folder=True, count_messages=True, recursive=False):
        """See interfaces.IMailFolder
        examples of calls : 
        >>> f = MailFolder()
        >>> f.getMailMessagesCount()
        0
        >>> f.getMailMessagesCount(True, False)
        0
        >>> f.getMailMessagesCount(False, True)
        0
        """
        providers = ()
        
        if count_folder:
            providers = providers+ (IMailFolder,)
                
        if count_messages:
            providers = providers+ (IMailMessage,)
            
        count = 0
        
        if len(providers) > 0:            
            for element in self.objectValues():
                for provider in providers :
                    if provider.providedBy(element):
                        count += 1
                if recursive:
                    if IMailFolder.providedBy(element):
                        count += element.getMailMessagesCount(count_folder,
                            count_messages, recursive)                                       
        return count
            
    
    def checkMessages(self):
        """See interfaces.IMailFolder     
        """
        raise NotImplementedError        
    
    def getServerName(self):
        """"See interfaces.IMailFolder      
        """
        return self.server_name
        
    def setServerName(self, server_name):
        """"See interfaces.IMailFolder      
        >>> f = MailFolder()
        >>> f.setServerName('INBOX.trash')
        >>> f.getServerName()
        'INBOX.trash'
        """
        # useful if we need some action when renaming server_name
        # typically resync
        self.server_name = server_name 
    
    
    def _addMessage(self, uid='', msg_key=''):
        """"See interfaces.IMailFolder              
        """
        if uid == '':
            uid = uniqueId(self, self.mail_prefix)
        else:                                
            uid = makeId(uid)                    
            
        new_msg = MailMessage(uid, uid, msg_key)
        self._setObject(new_msg.getId(), new_msg)
        return new_msg
        
        
    def _addFolder(self, uid='', server_name=''):  
        """"See interfaces.IMailFolder      
        """
        if uid == '':
            uid = uniqueId(self, 'folder_')
        else:                                
            uid = makeId(uid) 
        
        new_folder = MailFolder(uid, server_name)
        self._setObject(new_folder.getId(), new_folder)
        return new_folder 

    def findMessage(self, msg_key, recursive=True):
        """ See interfaces.IMailFolder      
        """
        # XXX see for caching here        
        message_list = self.getMailMessages(False, True, recursive)
        
        for message in message_list:
            if message.msg_key == msg_key:
                return message
        
        return None
        
    def childFoldersCount(self):     
        """ See interfaces.IMailFolder      
        """
        return self.getMailMessagesCount(True, False, False)
          
        
                           
""" classic Zope 2 interface for class registering
"""        
manage_addMailFolder = PageTemplateFile(
    "www/zmi_addmailfolder", globals(),
    __name__ = 'manage_addMailFolder')
    
def manage_addMailFolder(container, id=None, server_name ='', 
        REQUEST=None, **kw):
    """Add a calendar to a container (self).
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
        