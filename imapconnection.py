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

"""
    IMAPConnection : IMAP 4 rev 1 implementation for BaseConnection

"""
import re
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT
from zope.interface import implements
from interfaces import IConnection
from baseconnection import BaseConnection
from baseconnection import LOGIN_FAILED
from baseconnection import ConnectionError
from baseconnection import ConnectionParamsError
from baseconnection import CANNOT_SEARCH_MAILBOX, MAILBOX_INDEX_ERROR

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
            is_ssl = str(params['SSL']) == '1'
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
            raise ConnectionError(LOGIN_FAILED + ' for user %s' % user)

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

    def fetchPartial(self, mailbox, message_number, message_part, start, length):
        """ see interface for doc
        """
        result = ''
        self._respawn()
        self._connection.select(mailbox)

        try:
            imap_result =  self._connection.partial(message_number, \
                message_part, start, length)
        except self._connection.error:
            raise ConnectionError(CANNOT_SEARCH_MAILBOX % mailbox)
        except IndexError:
            raise ConnectionError(MAILBOX_INDEX_ERROR % (message_number, mailbox))

        if imap_result[0] == 'OK':
            imap_raw = imap_result[1]

            return imap_raw
        return results

    def partQueriedList(self, message_parts):
        """ creates a list of part queried
        """
        len_mp = len(message_parts)
        if len_mp <= 2:
            return []
        mp = message_parts[1:len_mp-1]
        return mp.split(' ')

    def extractResult(self, query, results):
        """ extracts a result from a block of results
        """
        # at ths time it's done "case by case"
        if query == 'FLAGS':
            raw = results[0][0]
            # todo use regexprs
            index = raw.find('FLAGS (')+7
            if index < 7:
                return ''
            else:
                out = raw.find(')')
                flags = raw[index:out].replace('\\','')
                return flags.split(' ')

        if query == 'RFC822.SIZE':
            raw = results[0][0]
            # todo use regexpr
            index = raw.find('RFC822.SIZE ')+12
            raw = raw[index:]
            out = raw.find(' ')
            return raw[:out]

        if query == 'RFC822.HEADER':
            if len(results[0]) <= 1:
                raise str(results)
            raw = results[0][1]
            raw_parts = raw.split('\r\n')
            i  = 0
            returned = {}
            for raw_part in raw_parts:
                raw_part = raw_part.strip()
                if raw_part == '':
                    continue
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
            return returned
        if query == 'RFC822':
            return results[0][1]

        raise NotImplementedError('%s : %s' % (query, results))

    def fetch(self, mailbox, message_number, message_parts):
        """ see interface for doc
        """
        query_list = self.partQueriedList(message_parts)
        if len(query_list) == 0:
            return {}

        self._respawn()
        results =  []

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
        except IndexError:
            raise ConnectionError(MAILBOX_INDEX_ERROR % (message_number, mailbox))

        if imap_result[0] == 'OK':
            imap_raw = imap_result[1]
            results = []
            i = 0
            for query in query_list:
                raw_result = self.extractResult(query, imap_raw)
                results.append(raw_result)
                i += 1
        if len(results) == 1:
            return results[0]
        return results

    def search(self, mailbox, charset, *criteria):
        """See interface for doc.
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
            # XXX try to parse errors
            raise ConnectionError(imap_result[1])
        else:
            imap_results = imap_result[1]
            for res in imap_results:
                if res.strip() != '':
                    results.extend(res.split(' '))

        return results

    def noop(self):
        """
        >>> f = IMAPConnection({'HOST': 'my.host', 'connection_type': 'IMAP'})
        >>> f.noop()
        """
        self._respawn()
        self._connection.noop()

    def writeMessage(self, mailbox, raw_message):
        """ writes a message
        """
        self._respawn()
        res = self._connection.append(mailbox, None , None, raw_message)
        try:
            # XXX not elegant
            res = res[1][0]
            res = res.split()
            res = res[2]
            return res.replace(']', '')
        except IndexError:
            return ''

    def rename(self, oldmailbox, newmailbox):
        """ renames a mailbox
        """
        self._respawn()
        res = self._connection.rename(oldmailbox, newmailbox)
        #### need to scan result here
        return res[0] == 'OK'

    def copy(self, from_mailbox, to_mailbox, message_number):
        """ copy a message from a folder to another
        """
        self._respawn()
        self._connection.select(from_mailbox)
        res = self._connection.uid('COPY', message_number, '"'+to_mailbox+'"')

        try:
            if res[1][0] == 'Over quota':
                raise ConnectionError('folder quota exceeded')
        except IndexError:
            pass

        return res[0] == 'OK'

    def create(self, mailbox):
        self._respawn()
        res = self._connection.create(mailbox)
        return res[0] == 'OK'



connection_type = 'IMAP'

def makeMailObject(connection_params):
    newob =  IMAPConnection(connection_params)
    uid = connection_params['uid']
    password = connection_params['password']
    #newob.login(uid, password)
    #print str('created '+str(newob))
    return newob


