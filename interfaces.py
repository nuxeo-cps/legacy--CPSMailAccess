# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# -*- encoding: iso-8859-15 -*-
# Author: Florent Guillaume <fg@nuxeo.com>
#         Tarek Ziad� <tz@nuxeo.com>
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
from zope.schema import Field, Text, List

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

    def getMailBox():
        """ returns mailbox holder
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

class IMapping(IContainer):

    def __len__():
        """Return the total number of items """

    def __getitem__(name):
        """Get an item value.
        """

    def __setitem__(name, val):
        """Set the value of an item
        """

    def __delitem__(name):
        """Delete all occurrences of an item, if present

        Does not raise an exception if the item is missing.
        """

    def __contains__(name):
        """ check if contains
        """

    def has_key(name):
        """Return true if the object contains the item."""

    def keys(self):
        """Return a list of all items
        """

    def values():
        """Return a list of all items values.
        """

    def items():
        """Return a list of all items and values.
        """


class IMailMessageMapping(IMapping):

    def get(name, failobj=None):
        """Get a header value.

        Like __getitem__() but return failobj instead of None when the field
        is missing.
        """

class IMailBox(IContainer):
    """ mailboxes gives a few api to synchronize
    """
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

class IMailTool(IContainer):
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
        """ message search interface
        """

    def fetch(mailbox, message_number, message_parts):
        """ fetcher
        """

    def noop():
        """ null command sended to keep connection alive
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