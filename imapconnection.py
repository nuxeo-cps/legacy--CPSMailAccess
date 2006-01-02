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
from zLOG import LOG, DEBUG

import re
import socket
from time import sleep
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT

from zope.interface import implements
from zope.app.cache.ram import RAMCache

from interfaces import IConnection
from baseconnection import BaseConnection, ConnectionError, SOCKET_ERROR

def patch_open(self, host = '', port = IMAP4_SSL_PORT):
    """ protects webmails from:
          o timeoutsocket patching
          o Python SSL+timeout failure
    """
    self.host = host
    self.port = port

    # testing if timeoutsocket has patched socket
    if hasattr(socket, "_no_timeoutsocket"):
        self.sock = socket._no_timeoutsocket(socket.AF_INET,
                                             socket.SOCK_STREAM)
    else:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    LOG('SSL connection', DEBUG, 'ssl opening')
    self.sock.settimeout(None)
    self.sock.connect((host, port))
    self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)
    LOG('SSL connection', DEBUG, 'ssl opening done')

class IMAPConnection(BaseConnection):
    """ IMAP4 v1 implementation for Connection

    >>> f = IMAPConnection({'HOST': 'localhost'})
    >>> IConnection.providedBy(f)
    True
    """
    implements(IConnection)
    _connection = None
    timeout = 5.0

    def __init__(self, connection_params= {}):
        """
        >>> f = IMAPConnection({'HOST': 'my.host', 'connection_type': 'IMAP'})
        >>> f.connection_type
        'IMAP'
        """
        LOG('IMAPConnection', DEBUG, 'init')
        BaseConnection.__init__(self, connection_params)
        self._open()

    def _open(self):
        # instanciate a imap4 object
        params = self.connection_params
        host = params['HOST']
        if params.has_key('SSL'):
            is_ssl = params['SSL'] == 1
        else:
            is_ssl = 0
        if params.has_key('PORT'):
            port = params['PORT']
        else:
            if is_ssl:
                port = IMAP4_SSL_PORT
            else:
                port = IMAP4_PORT

        failures = 0
        connected = False

        if is_ssl:
            self._patch_imap()

        while not connected and failures < 2:
            try:
                if is_ssl:
                   self._connection = IMAP4_SSL(host, port)
                else:
                    self._connection = IMAP4(host, port)
                connected = True
            except (IMAP4.abort, socket.error, socket.sslerror), e:
                LOG('Connection failure', DEBUG, str(e))
                sleep(0.3)
                failures += 1

        if not connected:
            raise ConnectionError(SOCKET_ERROR)
        else:
            if not is_ssl:
                self._connection.socket().settimeout(self.timeout)
    #
    # Internal methods
    #
    def _patch_imap(self):
        IMAP4_SSL.open = patch_open

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

    def _selectMailBox(self, mailbox):
        self._connection.select(mailbox)

    #
    # Overriden methods
    #

    def _checkparams(self, params):
        """ this is used to check params
        """
        BaseConnection._checkparams(self, params)
        # extra paramcheck will fit here

    def login(self, user, password):
        """ see interface for doc """
        self._respawn()
        try:
            typ, dat = self._connection.login(user, password)
        except (IMAP4.error, IndexError, socket.timeout), e:
            raise ConnectionError(str(e))

        # _connection state is AUTH if login succeeded
        if typ == 'OK' :
            self.user = user
            self.password = password
            return True
        else:
            return False

    def relog(self):
        """ relogs """
        self._respawn()
        user = self.user
        password = self.password
        if self.logout():
            self._open()
            self.login(user, password)

    def logout(self):
        """ see interface for doc
        """
        self._respawn()
        typ = 'NO'
        retries = 0
        while retries < 3 and typ == 'NO':
            typ, dat = self._connection.logout()
            retries += 1

        if typ == 'BYE':
            self.user = None
            self.password = None
            return True
        else:
            return False

    def getState(self):
        self._respawn()
        return self._connection.state

    def list(self, directory='""', pattern='*'):
        """ see interface for doc
        """
        self._respawn()
        result = []
        separator_pattern = re.compile(r'(.*) "(\W)\" (.*)')

        imap_list = self._connection.list(directory, pattern)
        if imap_list[0] == 'OK':
            for element in imap_list[1]:

                if element is None:
                    continue
                folder = {}
                folder_attributes = []

                parts = separator_pattern.findall(element)
                if len(parts) != 1:
                    continue

                parts = parts[0]

                separator = parts[1]

                # first part contains attributes
                attributes = parts[0].strip('(')
                attributes = attributes.strip(')')
                attributes = attributes.split('\\')
                for attribute in attributes:
                    if attribute:
                        folder_attributes.append(attribute)
                folder['Attributes'] = folder_attributes

                # second part contains folder name
                folder['Name'] = parts[2].strip('"')

                # unifiying separator
                if separator != '.':
                    folder['Name'] = folder['Name'].replace(separator, '.')
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

    def partQueriedList(self, message_parts):
        """ creates a list of part queried """
        return self._extractCommands(message_parts)

    def _extractResult(self, query, results):
        """ extracts a result from a block of results """
        if isinstance(results, tuple):
            results = list(results)

        if query == 'FLAGS':
            try:
                if isinstance(results, list) or isinstance(results, tuple):
                    raw = results[0]
                else:
                    raw = results
            except TypeError:
                return []

            if raw is None:
                return ''

            # todo use regexprs
            if isinstance(raw, tuple):
                raw = raw[0]
            index = raw.find('FLAGS (')+7
            if index < 7:
                return ''
            else:
                out = raw.find(')')
                flags = raw[index:out].replace('\\','')
                return flags.split(' ')

        if query == 'RFC822.SIZE':
            try:
                if isinstance(results, list) or isinstance(results, tuple) :
                    raw = results[0]
                else:
                    raw =results
            except TypeError:
                return ''
            # todo use regexpr
            if isinstance(raw, tuple):
                raw = raw[0]
            index = raw.find('RFC822.SIZE ')+12
            raw = raw[index:]
            out = raw.find(' ')
            return raw[:out]

        if query == 'RFC822.HEADER':
            if isinstance(results, list) or isinstance(results, tuple):
                raw = results[1]
            else:
                raw = results
            return self._extractHeaders(raw)

        if query == 'RFC822':
            return results[0]

        if query == 'BODY' or query == 'BODYSTRUCTURE':
            # todo
            # parse message
            # XXX should be use by all sub cases
            if isinstance(results, list):
                results = results[0]

            # extract subpart if needed
            cindexstart = results.find('BODYSTRUCTURE (')
            if cindexstart == -1:
                cindexstart = results.find('BODY (')

            if cindexstart != -1:
                cindexstop = self._findClosingParenthesis(results, cindexstart)
                result = results[cindexstart:cindexstop]
            else:
                result = results

            result = self._parseIMAPMessage(result)

            # body structure
            if len(result) > 1:
                result = result[1]
            else:
                result = result[0]
            return result

        if query.startswith('BODY.PEEK'):
            parts = re.match(r'(BODY.PEEK\[)(.*)(\])', query).groups()
            command = parts[1]

            if command.startswith('HEADER.FIELDS'):
                try:
                    res = self._extractHeaders(results[1])
                except IndexError:
                    raise str(results)
            else:
                if isinstance(results, list) and results[1] == ')':
                    res = results[0][1]
                else:
                    if len(results) < 2:
                        return None
                    res = results[1]
            return res

        raise NotImplementedError('%s : %s' % (query, results))

    def _findClosingParenthesis(self, text, start):
        """ closing-finder pattern """
        opened = 0
        i = start + 1
        while i < len(text):
            char = text[i]
            if char == '(':
                opened += 1
            elif char == ')':
                if opened == 0:
                    return i
                else:
                    opened -= 1
            i+=1
        return -1

    def fetch(self, mailbox, message_number, message_parts):
        """ see interface for doc """
        # fetch works for unique message_number, in integer or string
        # or with several numbers, like : '1,2,3'
        if isinstance(message_number, int):
            message_number = str(message_number)

        query_list = self.partQueriedList(message_parts)
        if len(query_list) == 0:
            return {}

        self._respawn()
        results = {}

        try:
            self._selectMailBox(mailbox)
        except (IMAP4.error, IMAP4_SSL.error), e:
            raise ConnectionError(str(e))
        try:
            imap_result =  self._connection.uid('fetch', message_number, message_parts)
        except self._connection.error, e:
            raise ConnectionError(str(e))
        except IndexError, e:
            raise ConnectionError(str(e))
        except (AttributeError, IMAP4.error, IMAP4_SSL.error), e:
            raise ConnectionError(str(e))
        except socket.sslerror, e:
            self.relog()
            raise ConnectionError(str(e))

        if imap_result[0] == 'OK':
            imap_raw = imap_result[1]
            results = {}
            messages_queried = message_number.split(',')
            u = 0
            if len(messages_queried) == 1:
                if not isinstance(imap_raw, list):
                    imap_raw = [imap_raw]
                else:
                    imap_raw = [imap_raw[0]]
            else:
                fimap_raw = []
                i = 1
                while i < len(imap_raw):
                    fimap_raw.append(list(imap_raw[i-1]))
                    i += 2
                imap_raw = fimap_raw

            for sub_raw in imap_raw:
                # filtering not parsed parts
                if sub_raw == [')']:
                    continue
                message = messages_queried[u]
                sub_result = []
                i = 0
                for query in query_list:
                    raw_result = self._extractResult(query, sub_raw)
                    sub_result.append(raw_result)
                    i += 1
                results[message] = sub_result
                u += 1
        if len(results.keys()) == 1:
            results = results.values()[0]
            if isinstance(results, list) and len(results) == 1:
                results = results[0]
        return results

    def search(self, mailbox, charset, *criteria):
        """See interface for doc. """
        self._respawn()
        results = []
        self._selectMailBox(mailbox)
        try:
            imap_result =  self._connection.uid('search', charset, *criteria)
        except (self._connection.error, socket.error, socket.sslerror), e:
            raise ConnectionError(str(e))

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
        """ writes a message """
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
        self._selectMailBox(from_mailbox)
        res = self._connection.uid('copy', message_number, '"'+to_mailbox+'"')
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

    def getFlags(self, mailbox, message_number):
        """ return flags of a message """
        self._respawn()
        self._selectMailBox(mailbox)
        rep = self._connection.uid('fetch', message_number,'(FLAGS)')

        val = rep[-1][0]
        if val is None:
            return ''
        flags=re.sub(r'(.+)(FLAGS \()(.+)(\).+)', r'\3', val)
        if flags.find('UID')!=(-1):
            flags=" "
        return flags

    def setFlags(self, mailbox, message_number, flags):
        """ set flag of a message """
        self._respawn()
        self._selectMailBox(mailbox)
        _flags = []
        for flag in flags.keys():
            if flags[flag] == 1:
                name = flag
                if name != 'forwarded':
                    _flag = '\%s' % name
                else:
                    _flag = '$forwarded'
                _flags.append(_flag)

        _flags = '(%s)' % ' '.join(_flags)

        # we want to do this asynced
        try:
            self._connection.uid('store', message_number, 'FLAGS', _flags)
        except (IMAP4.error, IndexError), e:
            raise ConnectionError(str(e))

    def expunge(self):
        """ expunge and instantly relog """
        self._respawn()
        self._connection.expunge()
        #self._relog()

    def select(self, mailbox):
        """ select """
        self._respawn()
        self._selectMailBox(mailbox)

    def deleteMailBox(self, mailbox):
        """ delete mailbox """
        self._respawn()
        return self._connection.delete(mailbox)

    def _parseIMAPMessage(self, message):
        """ parses an imap message """
        message = message.lower()
        message = message.strip()
        start = 1
        subparts = []
        while start != -1:
            start = message.find('(')
            end = start
            if len(message) <= 1:
                break
            if start != -1:
                # finding the clossing bracket in the message
                # each time we find a ( we need to lety a ) go
                counter = 0
                end  = start + 1
                while end < len(message):
                    if message[end] == '(':
                        counter += 1
                    elif message[end] == ')':
                        if counter > 0:
                            counter -= 1
                        else:
                            # found it
                            break
                    end += 1

            if start != -1 and start != end:
                submessage = message[start:end+1]
                # now let's get into the body
                #submessage =

                subpart = self._parseIMAPMessage(submessage[1:-1])
                #
                # removes submessage
                message = message.replace(submessage, '')

                subparts.append(subpart)

        message_parts = self._quoteSplitting(message)
        message_parts = map(self._cleanpart, message_parts)

        # todo: inserted at the end, should be inserted on the right place
        if subparts != []:
            for subpart in subparts:
                message_parts.append(subpart)
        return message_parts

    def _quoteSplitting(self, element):
        """ will split from quote to quote

        without braking quotes, XXX see if regexpr is not simpler
        """
        split_points = []
        index = 0
        inquote = False
        while index < len(element):
            if element[index] == '"':
                inquote = not inquote
            elif element[index] == ' ' and not inquote:
                split_points.append(index)
            index += 1

        split_points.append(len(element))
        # now splitting
        splitted = []
        current = 0
        for split_point in split_points:
            value = element[current:split_point]
            if value.strip() != '':
                splitted.append(value)
            current = split_point + 1

        return splitted

    def _cleanpart(self, element):
        """ cleans a word """
        if element[0] == '"' and element[-1]=='"':
            return element.strip('"')
        else:
            if element == 'nil':
                return None
            else:
                try:
                    return int(element)
                except ValueError:
                    return element.strip()

    def getMessagePart(self, mailbox, message_number, part_number):
        """ retrieves a message part """
        return self.fetch(mailbox, message_number,
                          '(BODY.PEEK[%s])' % part_number)

    def getMessageStructure(self, mailbox, message_number):
        return self.fetch(mailbox, message_number, '(BODY)')

    def _extractInfos(self, infos, part):
        if infos[0] not in ('alternative', 'related'):
            if part != 1:
                return []
            return infos
        else:
            return infos[part]

    def getPartInfos(self, mailbox, message_number, part_number):
        structure = self.getMessageStructure(mailbox, message_number)
        return self._extractInfos(structure, part_number)

    def _extractCommands(self, command_sequence):
        """ extracts from a sequence commands

        XXX should use regexpr here
        """
        command_sequence = command_sequence.strip()
        if command_sequence == '' or len(command_sequence) <= 2:
            return []

        if command_sequence[0] == '(' and command_sequence[-1] == ')':
            command_sequence = command_sequence[1:-1]

        start = stop = i = 0
        commands = []
        level = 0
        while i <= len(command_sequence):
            if i == len(command_sequence):
                command = command_sequence[start:stop]
                commands.append(command)
            else:
                if command_sequence[i] == ' ':
                    if level == 0:
                        command = command_sequence[start:stop]
                        if command[0] == '(' and command[1] == ')':
                            command = command[1:-1]
                        commands.append(command)
                        start = stop + 1
                elif command_sequence[i] == '[': level += 1
                elif command_sequence[i] == ']': level -= 1
            stop += 1
            i += 1

        return commands

    def _extractHeaders(self, raw_headers):
        """ extracts headers retrieved from server """
        raw_parts = raw_headers.split('\r\n')
        i  = 0
        returned = []
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
            returned.append((raw_name, raw_data))
            i += 1
        return returned

    def getNextUid(self, mailbox):
        """ getnext uid from server

        if the server does not have UIDNEXT capability,
        we need to calculate it
        XXX see if it's notrisky, if we can lock it
        """
        self._respawn()
        self._selectMailBox(mailbox)
        res = self._connection.response('UIDNEXT')
        next_uid = res[1][0]
        if next_uid is not None:
            return next_uid
        else:
            res = self._connection.uid('search', None, 'ALL')
            if res[0] != 'OK':
                raise ConnectionError('could not list folder %s' % mailbox)
            else:
                uids = res[1][0]
                if uids == '':
                    return '1'

                uids = uids.split(' ')
                max_ = -1
                for uid in uids:
                    uid = int(uid)
                    if uid > max_:
                        max_ = uid
                return str(max_+1)

class CachedIMAPConnection(IMAPConnection):

    def _addCache(self, key, data):
        """ to be extern. in mailfolder """
        if not hasattr(self, '_cache'):
            self._cache = RAMCache()
        self._cache.set(data, key)

    def _getCache(self, key):
        """ to be extern. in mailfolder """
        if not hasattr(self, '_cache'):
            self._cache = RAMCache()
            return None
        elements = self._cache.query(key)
        return elements

    def getMessageStructure(self, mailbox, message_number):

        key = '%s.%s' %(mailbox, message_number)
        value = self._getCache(key)
        if value is None:
            value = IMAPConnection.getMessageStructure(self, mailbox,
                                                       message_number)
            self._addCache(key, value)
        return value

    def _getLastSelect(self):
        return self._getCache('SELECT')

    def _setLastSelect(self, value):
        self._addCache('SELECT', value)

    def _selectMailBox(self, mailbox):
        current_state = self.getState()
        if current_state == 'SELECTED':
            last = self._getLastSelect()
            if last != mailbox:
                IMAPConnection._selectMailBox(self, mailbox)
                self._setLastSelect(mailbox)
        else:
            IMAPConnection._selectMailBox(self, mailbox)
            self._setLastSelect(mailbox)

connection_type = 'IMAP'

def makeMailObject(connection_params):
    newob =  CachedIMAPConnection(connection_params)
    return newob
