#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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
# need to contralize timeoutsocket

# XXX need to make timeoutsocket comaptible with ssl sockets
from time import time
from zope.interface import implements

from interfaces import IConnection

has_connection = 1

class ConnectionError(Exception): pass
class ConnectionParamsError(Exception): pass

LOGIN_FAILED = 'Login Failed.'
CANNOT_SEARCH_MAILBOX = 'Could not search mailbox %s'
MAILBOX_INDEX_ERROR = '[%s] Message Index error in box %s'
BAD_LOGIN = 'Bad login'
NO_CONNECTOR = 'Could find a connector'
CANNOT_READ_MESSAGE = 'Could not read message %s in %s'
SOCKET_ERROR  = 'Could not open a socket to the server'

class BaseConnection:
    """ base class used for any mail server connexion
    """
    implements(IConnection)

    start_time = 0
    idle_time = 0
    connected = False
    uid = ''
    connection_type = ''
    connection_params = {}
    connection_timeout = 10
    connection_number = 0

    def __init__(self, connection_params = {}):

        self._checkparams(connection_params)

        self.start_time = float(time())
        if connection_params.has_key('uid'):
            self.uid = connection_params['uid']
        if connection_params.has_key('connection_type'):
            self.connection_type = connection_params['connection_type']

        #timeoutsocket.setDefaultSocketTimeout(self.connection_timeout)

    def _respawn(self):
        self.idle_time = 0

    def login(self, user, password):
        return False

    def logout(self):
        return False

    def isConnected(self):
        return self.connected

    def list(self, directory='""', pattern='*'):
        """ see interface
        """
        raise NotImplementedError

    def getacl(self, mailbox):
        """
            returns a list of acls for the given folder
            each acls contains two parts : who and what
            example :
                [{'what': '"acdilrsw"', 'who': '"owner"'}]
        """
        raise NotImplementedError


    def search(self, mailbox, charset, *criteria):
        """
            will perform a seach on the given mailbox
            with given charset and criteria
            returns a list of numbers
            from 1 to N,
            1 is the first mailbox message
        """
        raise NotImplementedError

    def fetch(self, mailbox, message_number, message_parts):
        raise NotImplementedError

    def fetchPartial(self, mailbox, message_number, message_part, start, length):
        raise NotImplementedError

    def noop(self):
        raise NotImplementedError

    def _checkparams(self, params):
        try:
            host = params['HOST']
        except KeyError:
            raise ConnectionParamsError('Host name is missing')

        self.connection_params = params

    def writeMessage(self, mailbox, raw_message):
        """ writes a message
        """
        raise NotImplementedError

    def rename(self, oldmailbox, newmailbox):
        """ renames a mailbox
        """
        raise NotImplementedError

    def copy(self, from_mailbox, to_mailbox, message_number):
        """ copy a message from a box to another
        """
        raise NotImplementedError

    def create(self, mailbox):
        raise NotImplementedError

    def deleteMailBox(self, mailbox):
        raise NotImplementedError

    def relog(self):
        raise NotImplementedError
