# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
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
""" MailPart

    A MailPart is a part of a message
"""
from zLOG import LOG, INFO, DEBUG

from zope.interface import implements
from interfaces import IMailPart
from email import Message as Message
from email import message_from_string
from email.Charset import Charset
from email.Header import decode_header
from Globals import InitializeClass
from OFS.Folder import Folder

class MailPart(Folder):
    """ A Mail part encapsulates a python message
        it is generated on the fly when needeed
        and adapts the message
    >>> f = MailPart('my_part', None, None)
    >>> IMailPart.providedBy(f)
    True
    """
    implements(IMailPart)
    msg = None
    _v_part = None

    def __init__(self, id, message, part):
        self.id = id
        self.msg = message
        self._v_part = part
        self.cache_level = 1

    def copyFrom(self, msg):
        """ make a copy """
        self.msg = msg.msg
        self._v_part = msg._v_part
        self.cache_level = msg.cache_level

    def _getStore(self):
        return  self._v_part

    def _setStore(self, store):
        self._v_part = store

    def getParent(self):
        """ returns the message instance """
        return self.msg

    def getRawMessage(self):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        payload = store._payload
        return store.as_string()

    def getFileInfos(self):
        """ returns the filename if the part is a file

        Otherwise return an empty string
        """
        store = self._getStore()
        if type(store) is str:
            return None
        filename = store.get_filename() or store['filename']
        if filename is None:
            return None
        mimetype = store['Content-Type']
        if mimetype is None:
            mimetype = 'unknown'
        if mimetype.find(';'):
            mimetype = mimetype.split(';')[0]
        # todo: add size
        return {'filename' : filename,
                'mimetype' : mimetype}

    def isMultipart(self):
        """ See interfaces.IMailMessage
        >>> f = MailPart('id', None, None)
        >>> f.cache_level = 2
        >>> f.loadMessage('mmdclkdshkdjg')
        >>> f.isMultipart()
        False
        """
        store = self._getStore()
        return store.is_multipart()

    def getPartCount(self):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        if self.isMultipart():
            return len(store.get_payload())
        else:
            return 1

    def getPart(self, index=0, decode= False):
        """ See interfaces.IMailMessage """
        if self.isMultipart():
            return self._getStore().get_payload(index)
        else:
            return self._getStore()

    def setPart(self, index, content):
        """ See interfaces.IMailMessage """
        multi = self.isMultipart()
        store = self._getStore()
        if not multi:
            store._payload = content
        else:
            payload = store._payload
            if index < len(payload):
                store._payload[index] = content
            elif index == 0 and len(payload) == 0:
                store._payload.append(content)

    def getParts(self):
        """ returns parts in a sequence

        (or a string if monopart)
        """
        store = self._getStore()
        return store.get_payload()


    def getCharset(self, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        return store.get_charsets()[part_index]

    def setCharset(self, charset, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        ob_charset = Charset(charset)

        if not self.isMultipart():
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_charset(ob_charset)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_charset(ob_charset)

    def getContentType(self, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_content_type()
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_content_type()

    def setContentType(self, content_type, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_type(content_type)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_type(content_type)


    def getParams(self, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_params()
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_params()

    def getParam(self, param_name, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_param(param_name)
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_param(param_name)

    def setParam(self, param_name, param_value, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_param(param_name, param_value)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_param(param_name, param_value)

    def delParam(self, param_name, part_index=0):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.del_param(param_name)
        else:
            payload = store.get_payload()
            payload[part_index-1].del_param(param_name)

    def getHeaders(self):
        """ Get a message headers """
        store = self._getStore()
        res = {}
        for header in store._headers:
            res[header[0]] = header[1]
        return res

    def getHeader(self, name):
        """ Get a message header. """
        store = self._getStore()

        elements = store.get_all(name, [])
        if elements is None:
            return []
        return elements

    def setHeader(self, name, value):
        """ Set a message header. """
        store = self._getStore()
        while store.has_key(name):
            # Erase previous header
            del store[name]
        store[name] = value

    def addHeader(self, name, value):
        """ adds an header """
        store = self._getStore()
        store[name] = value

    def removeHeader(self, name, values=None):
        """ removes header """
        store = self._getStore()
        headers = self.getHeader(name)
        if values is None:
            while store.has_key(name):
                # Erase previous header
                del store[name]
        else:
            for item in values:
                if item in headers:
                    headers.remove(item)
            if headers != values:
                while store.has_key(name):
                    # Erase previous header
                    del store[name]
                for value in headers:
                    self.addHeader(name, value)

    def loadMessage(self, raw_msg):
        """ See interfaces.IMailMessage
        """
        ### XXX we'll do different load level here
        if self.cache_level == 0:
            # todo
            raise NotImplementedError
        elif self.cache_level == 1:
            # raw_msg is a list of 3 elements : flags, size and headers
            if type(raw_msg) is list:
                flags = raw_msg[0]
                size = raw_msg[1]
                headers = raw_msg[2]
            else:
                headers = raw_msg
                flags = ''
                size = ''

            self._setStore(Message.Message())
            store = self._getStore()
            # filling headers
            for key in headers.keys():
                store[key] = headers[key]
            self._parseFlags(flags)
            # todo: manage size
        else:
            if type(raw_msg) is list:
                # raw_msg is a list of 2 elements : flags, body
                flags = raw_msg[0]
                body = raw_msg[1]
            else:
                flags = ''
                # body shall content headers also
                body = raw_msg
            store = message_from_string(body)
            self._setStore(store)
            self._parseFlags(flags)

    def _parseFlags(self, flags):
        """ no flags in parts at this time """
        pass

    def getPersistentPartIds(self):
        """ retrieves a sequence of persistent parts """
        results = []
        i = 0
        for element in self.getParts():
            if element is not None:
                results.append(i)
            i += 1
        return results

    def deletePart(self, part_num):
        """ deletes the given part

        Get back to a simple mail if there's one part left
        """
        if not self.isMultipart() or part_num>=self.getPartCount():
            return False
        store = self._getStore()
        part_count = self.getPartCount()
        new_payload = []
        for part in range(part_count):
            if part != part_num:
                new_payload.append(store.get_payload(part))

        if len(new_payload) > 1:
            # still multipart
            store._payload = new_payload
        else:
            # back to simple message
            store._payload = new_payload[0]
        return True

    def getDirectBody(self):
        """ returns direct body
        """
        if self.getPartCount() > 0 and not self.isMultipart():
            store = self._getStore()
            return store._payload
        else:
            return ''


InitializeClass(MailPart)

