#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
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

"""
    IMAPConnection : IMAP 4 rev 1 implementation for BaseConnection

"""
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT

from zope.interface import implements
from interfaces import IConnection
from baseconnection import BaseConnection
from baseconnection import LOGIN_FAILED
from baseconnection import ConnectionError
from baseconnection import ConnectionParamsError
from baseconnection import CANNOT_SEARCH_MAILBOX

class IMAPConnection(BaseConnection):
    """ IMAP4 v1 implementation for Connection

    >>> f = IMAPConnection({'HOST': 'localhost'})
    >>> IConnection.providedBy(f)
    True
    """
    implements(IConnection)
    _connection = None
    _selected_mailbox = None


    def __init__(self, connection_params= {}):
        """
        >>> f = IMAPConnection({'HOST': 'my.host', 'connection_type': 'IMAP'})
        >>> f.connection_type
        'IMAP'
        """
        BaseConnection.__init__(self, connection_params)

        # instanciate a imap4 object
        params = self.connection_params

        host = params['HOST']

        if params.has_key('SSL'):
            is_ssl =  params['SSL'] == 1
        else:
            is_ssl = 0

        if params.has_key('PORT'):
            port = params['PORT']
        else:
            if is_ssl:
                port = IMAP4_SSL_PORT
            else:
                port = IMAP4_PORT


        if is_ssl:
            self._connection = IMAP4_SSL(host, port)
        else:
            self._connection = IMAP4(host, port)

    #
    # Internal methods
    #

    def _isSSL(self):
        """
        >>> f = IMAPConnection({'HOST': 'my.host', 'connection_type': 'IMAP'})
        >>> f._isSSL()
        False
        >>> f = IMAPConnection({'SSL': 1, 'HOST': 'my.host', 'connection_type': 'IMAP'})
        >>> f._isSSL()
        True
        """
        if self._connection:
            if isinstance(self._connection, IMAP4_SSL):
                return True
        return False

    #
    # Overriden methods
    #

    def _checkparams(self, params):
        """ this is used to check params
        """
        BaseConnection._checkparams(self, params)

        # extra paramcheck will fit here

    def login(self, user, password):
        """ see interface for doc
        """
        self._respawn()
        try:
            typ, dat = self._connection.login(user, password)
        except self._connection.error:
            raise ConnectionError(LOGIN_FAILED)

        # _connection state is AUTH if login succeeded
        if typ == 'OK' :
            self.connected = True
            return True
        else:
            return False

    def logout(self):
        """ see interface for doc
        """
        self._respawn()
        typ, dat = self._connection.logout()

        if typ == 'BYE' :
            self.connected = False

    def list(self, directory='""', pattern='*'):
        """ see interface for doc
        """
        self._respawn()
        result = []
        imap_list = self._connection.list(directory, pattern)
        if imap_list[0] == 'OK':
            for element in imap_list[1]:

                if element is None:
                    continue
                folder = {}
                folder_attributes = []
                parts = element.split(' "." ')
                # first part contains attributes
                attributes = parts[0].strip('(')
                attributes = attributes.strip(')')
                attributes = attributes.split('\\')
                for attribute in attributes:
                    if attribute:
                        folder_attributes.append(attribute)
                # second part contains folder name
                folder['Attributes'] = folder_attributes
                folder['Name'] = parts[1].strip('"')
                result.append(folder)
        return result

    def getacl(self, mailbox):
        """ see interface for doc
        """
        self._respawn()
        result = []
        imap_acl = self._connection.getacl(mailbox)
        if imap_acl[0] == 'OK':
            # see if we have other variants
            acls = imap_acl[1]

            for acl in acls:
                current = {}

                acls_parts = acl.split(" ")
                # first part is the folder

                # second part is who
                current['who'] = acls_parts[1].strip('"')

                # third part is what
                current['what'] = acls_parts[2].strip('"')

                result.append(current)
        return result

    def fetch(self, mailbox, message_number, message_parts):
        """ see interface for doc
        """
        self._respawn()
        results =  {}
        # XXX forcing each time but
        # we should select mailbox once for all
        # like in the commented code
        #if self._selected_mailbox <> mailbox:
        #    self._connection.select(mailbox)
        #    self._selected_mailbox = mailbox
        self._connection.select(mailbox)

        try:
            imap_result =  self._connection.fetch(message_number, message_parts)
        except self._connection.error:
            raise ConnectionError(CANNOT_SEARCH_MAILBOX % mailbox)

        if imap_result[0] == 'OK':
            imap_raw = imap_result[1]
            # raw imap results looks like this : 1 (UID 1)
            # we want to get the number after (UID
            #for raw_content in imap_raw:
            #try:
            if imap_raw is list:
                for element in imap_raw:
                    # this is the cool part : we are going
                    # to generalize imap datas
                    element_list = self._generalize(element)
            elif imap_raw is tuple:
                for element in imap_raw:
                    # this is the cool part : we are going
                    # to generalize imap datas
                    element_list = self._generalize(element)
            else :
                element_list = self._generalize(imap_raw)

        #except:
            results = element_list

        return results

    def _generalize(self, element):
        """
            this definitely needs to be externalized
            in an external file
            as a "generalization grammar"
            based on regular expression
            for transformation
        """
        returned = {}
        str_element = str(element)

        if str_element.find('(UID') >= 0:
            element = str_element.split('(UID ')[1]
            element = element.split(')')[0]
            element = element.strip()
            returned['UID'] = element

        elif str_element.find('RFC822.HEADER') >= 0:
            parts = []
            raw_part = element[0][1]
            raw_parts = raw_part.split('\r\n')

            # todo : find the name
            i  = 0
            for raw_part in raw_parts:
                raw_part = raw_part.strip()
                first_semicolumn = raw_part.find(':')
                if first_semicolumn == -1:
                    first_semicolumn = raw_part.find('=')
                #raw_parts = raw_part.split(':')
                if first_semicolumn > -1:
                    raw_name = raw_part[0:first_semicolumn].strip()
                    raw_data = raw_part[first_semicolumn+1:].strip()
                else:
                    raw_name = raw_part
                    raw_data = ''
                returned[raw_name] = raw_data
                i += 1
        else:
            returned[element] = element
        return returned

    def search(self, mailbox, charset, *criteria):
        """ see interface for doc
        """
        self._respawn()
        results = []

        # XXX forcing each time but
        # we should select mailbox once for all
        # like in the commented code
        #if self._selected_mailbox <> mailbox:
        #    self._connection.select(mailbox)
        #    self._selected_mailbox = mailbox
        self._connection.select(mailbox)

        try:
            imap_result =  self._connection.search(charset, *criteria)
        except self._connection.error:
            raise ConnectionError(CANNOT_SEARCH_MAILBOX % mailbox)

        if imap_result[0] == 'NO':
            raise ConnectionError(imap_result[1])
        else:
            imap_results = imap_result[1]
            i_results = []
            for result in imap_results:
                if result:
                    i_results = results + result.split(' ')
        # we want ints
        for item in i_results:
            results.append(int(item))
        return results

    def noop(self):
        """
        >>> f = IMAPConnection({'HOST': 'my.host', 'connection_type': 'IMAP'})
        >>> f.noop()
        """
        self._respawn()
        self._connection.noop()

connection_type = 'IMAP'

def makeMailObject(connection_params):
    newob =  IMAPConnection(connection_params)
    uid = connection_params['uid']
    password = connection_params['password']
    #newob.login(uid, password)
    #print str('created '+str(newob))
    return newob


