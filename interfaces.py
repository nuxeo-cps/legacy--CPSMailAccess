# Copyright (c) 2004-2005 Nuxeo SARL <http://nuxeo.com>
# -*- encoding: iso-8859-15 -*-
# Author: Florent Guillaume <fg@nuxeo.com>
#         Tarek Ziadé <tz@nuxeo.com>
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
from zope.interface.common.mapping import IMapping
from zope.app.container.interfaces import IContained, IContainer
from zope.app.container.constraints import ContainerTypesConstraint
from zope.app.traversing.interfaces import ITraverser
from zope.schema import Field, Text, List

class IMailFolder(IContainer):
    """A container of mail messages and other mail folders.
    """
    server_name = Field(
        title=u'Server Name',
        description=u'Corresponding server name',
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

    def _synchronizeFolder():
        """ synchronizes the Folder and its content with the server
            uses checkMessages depending on cache strategies
        """

    def getServerName():
        """" returns server name
        """

    def setServerName(self, server_name):
        """" sets server name
             can also hold a synchronization call
             when the name changes
        """


    def _addMessage(uid='', digest=''):
        """ Mail Message factory for this
            MailFolder, adds an IMailMessage
            to it and returns it
        """

    def _addFolder(uid='', server_name=''):
        """ Mail Folder factory for this
            MailFolder, adds an IMailFolder
            to it and returns it
        """

    def childFoldersCount():
        """ returns the number of child fodlers
        """

    def getMailBox():
        """ returns mailbox holder
        """

    def rename(new_name):
        """ renames the folder
        """


class IMailMessage(IContainer):
    """A mail message.

    It stores the content of a message, this content can be composed of
    headers, ID, and optionnaly the body.
    """
    uid = Field(
        title=u'Message ID',
        description=u'Unique identifier for message in its container',
        default=u'',
        required=True)

    digest = Field(
        title=u'Message Digest',
        description=u'Digest used to uniquely identify message',
        default=u'',
        required=False)

    def attachFile(file):
        """ attacha file to the message
        """

class IMailBox(IContainer):
    """ mailboxes gives a few api to synchronize
    """

    """ indicates the cache level used by
        the mailbox
        0 : no cache
        1 : headers cached
        2 : full cache (slow)
    """
    cache_level = Field(
        title=u'Cache level',
        description=u'Indicates the cache level for this mailbox',
        default=u'',
        required=True)

    connection_params = List(
        title=u'Connection parameters',
        description=u'Connection parameters properties',
        readonly=False,
        required=False)

    def synchronize():
        """ synchronizes the mailbox and its content
            and its content with the server by recursive calls to synchronizeFolder
        """

    def _getconnector():
        """ used to get a server connection object
        """

    def setParameters(connection_params, resync=True):
        """ sets connections parameters
            if resync is True, resyncs with the server
        """

    def setTreeViewCache(treeview):
        """ sets a non persistent value
            used to keep a calculated treeview
        """

    def getTreeViewCache():
        """ retrieves the cached treeview
        """

    def clearTreeViewCache():
        """ empty the cache
        """

    def sendMessage(msg_from, msg_to, msg_subject, msg_body,
            msg_attachments):
        """ creates a message, sends it and copy it to Send folder
        """

class IMailTool(Interface):
    """ portal tool
    """
    def listConnectionTypes():
        """ returns a list of founded connection
            types, based on what plugins have been successfully
            scanned
        """

    def reloadPlugins():
        """ rescan avalailable connection plugins
        """

    def killConnection(uid, connection_type):
        """ kills a given connection
        """

    def killAllConnections():
        """ kills all connections
        """

class IConnection(Interface):
    """ important a mail folder is called an mailbox in IConnection
    """

    def login(user, password):
        """ used to login
        """

    def logout():
        """ used to logout
        """

    def isConnected():
        """ used to check the state
        """

    def list(directory='""', pattern='*'):
        """ returns a flat list of directories
            each directory is a dict
            with two keys :
                Name : Name of the directory (full path)
                    example: 'INBOX.Drafts'__init__(self, initlist=None):
                Attributes : List of attributes
                    example : ['Unmarked', 'HasChildren']
        """

    def getacl(mailbox):
        """ returns a list of acls for the given folder
            each acls contains two parts : who and what
            example :
                [{'what': '"acdilrsw"', 'who': '"owner"'}]
        """

    def search(mailbox, charset, *criteria):
        """Search messages.

        Returns a list of message uids (strings).
        """

    def fetch(mailbox, message_number, message_parts):
        """ fetcher
        """

    def noop():
        """ null command sended to keep connection alive
        """

    def writeMessage(mailbox, raw_message):
        """ writes a message to the given mailbox
        """

    def fetchPartial(mailbox, message_number, message_part, start, length):
        """ gets a part of a message
        """

    def rename(oldmailbox, newmailbox):
        """ renames a mailbox
        """
    def copy(from_mailbox, to_mailbox, message_number):
        """ copy a message from a box to another
        """

class IConnectionList(Interface):

    def listConnectionTypes():
        """ returns a list of connection types
        """

    def registerConnectionType(connection_type, method):
        """ registers a newconnectino type thru a given method
        """

    def getConnection(connection_params):
        """ gets a connection for the current user
        """

    def killConnection(uid, connection_type):
        """ kills a given connection
        """

    def killAllConnections():
        """ kills all connections
        """

class IConnectionWatcher(Interface):

    sleep_time = Field(
        title=u'Sleep Time',
        description=u'Sleep time for the thread',
        default=u'',
        required=True)

    idle_time = Field(
        title=u'Idle Time',
        description=u'Time limit for connections',
        default=u'',
        required=True)

    def linkConnectionList(connection_list):
        """ links the connection to watch
        """

    def run():
        """ runs the guard
        """
    def stop():
        """ stops the guard
        """

class IMailRenderer(Interface):

    def renderBody(mail, part_index):
        """ renders a human readable body
            from given part
        """

class IMailMessageCache(Interface):
    """Cache used to hold temporary mail messages.

    This is useful to hold deleted message during synchronization
    when the may actually have been just moved.

    This cache is keyed by a digest which is usually based on the
    headers only.
    """
    def clear():
        """Clear the message cache."""

    def get(digest, default=None, remove=False):
        """Get a message and maybe delete it from the cache."""

    def __getitem__(digest):
        """Get a message.

        Returns None if the message is not present
        """

    def __setitem__(digest, message):
        """Put a message in the cache."""

    def has_key(digest):
        """Check if a message is in the cache."""

    def __len__():
        """Get the number of messages cached."""

class IMessageTraverser(ITraverser):
    """ Traversable interface, used to render
        parts of a message according to the given url
        useful to manage parts that are cached, on server, or stocked
    """
    def traverse(name, furtherPath):
        """ traverses the message to render the right part
        """

class IMailPart(Interface):
    """ IMailPart is an adapter that presents a python message object
    """
    def getRawMessage():
        """ retrieves the raw message
        """

    def getFileInfos():
        """ returns a dictionnary with info on the file
            None if not a file
        """

    def isMultipart():
        """ tells if the mail is multipart
        """

    def getPartCount():
        """ returns the number of parts the message holds
        """

    def getPart(self, index=0):
        """ returns the given index part
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

    def getContentTypeParams(part_index=0):
        """ gets the content type param list as tuple
            for single part messages, part_index is 0
        """

    def getParams(part_index=0):
        """ gets params in tuple (name, value)
            for single part messages, part_index is 0
        """

    def getParam(param_name, part_index=0):
        """ gets value for given param
            for single part messages, part_index is 0
        """

    def setParam(param_name, param_value, part_index=0):
        """ sets the param to given value
            for single part messages, part_index is 0
        """

    def delParam(param_name, part_index=0):
        """ deletes the given param
            for single part messages, part_index is 0
        """

    def setPart(self, index, content):
        """ sets a part
        """

    def loadMessage(raw_msg):
        """ loads a message from a string raw content
        """
