# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
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

from zope.interface import Interface
from zope.app.container.interfaces import IContained, IContainer
from zope.app.container.constraints import ContainerTypesConstraint
from zope.schema import Field, Text


class IMailFolder(IContainer):
    """A container of mail messages and other mail folders.
    """
    server_name = Field(
        title=u'Server Name',
        description=u'Corresponding server name',
        default=u'',
        required=False)
        
    mail_prefix = Field(
        title=u'Prefix for mail objects',
        description=u'All mails are prefixed with this',
        default=u'',
        required=False)        
        
    def getMailMessages(list_folder=True, list_messages= True, recursive=False):
        """Retrieves all contained messages and/or folders

        Returns a sequence of IMailMessage and/or IMailFolder.
        """
        
    def getMailMessagesCount(recursive=False):
        """ Retrieves a count of all contained messages        
        
        """
        
    def checkMessages():
        """ Each Mail Folder can resync its content
            according to server's folder
            a global resync would be a resync done on 
            the root mail folder
        """
        
    def getServerName():
        """" returns server name
        """
        
    def setServerName(self, server_name):        
        """" sets server name
             can also hold a synchronization call
             when the name changes
        """
        
        
    def _addMessage(uid='', msg_key=''):
        """ Mail Message factory for this
            MailFolder, adds an IMailMessage
            to it and returns it
        """
        
    def _addFolder(uid='', server_name=''):
        """ Mail Folder factory for this
            MailFolder, adds an IMailFolder
            to it and returns it
        """        
        
    def findMessage(msg_key, recursive=True):
        """ finds a message by its msg_key
        """ 
        
    def childFoldersCount():
        """ returns the number of child fodlers
        """           
            
class IMailMessage(IContainer):
    """A mail message.

    It stores the content of a message, this content can be composed of
    headers, ID, and optionnaly the body.
    """
    msg_uid = Field(
        title=u'Message ID',
        description=u'Unique identifier for message in its container',
        default=u'',
        required=True)
        
    msg_key = Field(
        title=u'Message Key',
        description=u'Hash key used to identify message',
        default=u'',
        required=False)
       
        
        
class IMailMessageStore(IContainer):
    """ Provides interface to a mail message store
        
    """                
    def loadMessage(raw_msg):
        """ loads a message from a string raw content  
        """
        
    def getPartCount():
        """ returns the number of parts the message holds
        """         
        
    def getCharset(part_index=0):        
        """ returns the charset for the given part
            for single part messages, part_index is 0
        """
        
    def setCharset(charset, part_index=0):        
        """ sets the charset for the given part 
            for single part messages, part_index is 0       
        """        
        
    def isMultipart():         
        """ tells if the mail is multipart
        """
        
    def getContentType(part_index=0):
        """ retrieves the content type
            for single part messages, part_index is 0       
        """      
        
    def setContentType(content_type, part_index=0):
        """ sets the content type
            for single part messages, part_index is 0       
        """      
               