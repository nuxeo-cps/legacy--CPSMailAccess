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
from zope.interface import implements
from interfaces import IMailPart
from email import Message as Message
from email import message_from_string
from email.Charset import Charset
from email.Header import decode_header
from Globals import InitializeClass

class MailPart:
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
    id = ''
    cache_level = 1

    def __init__(self, id, message, part):
        self.id = id
        self.msg = message
        self._v_part = part

    def _getStore(self):
        return  self._v_part

    def _setStore(self, store):
        self._v_part = store

    def getParent(self):
        """ returns the message instance
        """
        return self.msg

    def getRawMessage(self):
        """ see interface
        """
        store = self._getStore()
        return store.as_string()

    def isMultipart(self):
        """ See interfaces.IMailMessage
        >>> f = MailPart('id', None, None)
        >>> f.cache_level = 0
        >>> f.loadMessage('mmdclkdshkdjg')
        >>> f.isMultipart()
        False
        """
        store = self._getStore()
        return store.is_multipart()

    def getPartCount(self):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if self.isMultipart():
            return len(store.get_payload())
        else:
            return 1

    def getPart(self, index=None, decode= False):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if index == None:
            try:
                part = store.get_payload(None, decode)
            except TypeError:
                part = None
        else:
            try:
                part = store.get_payload(index, decode)
            except TypeError:
                part = None

        return part

    def setPart(self, index, content):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        payload = store.get_payload(index, False)
        if content is not None:
            payload.set_payload(content)
        else:
            store._payload[index] = None


    def getParts(self):
        """ returns parts in a sequence (or a string if monopart)
        """
        store = self._getStore()
        return store.get_payload()


    def getCharset(self, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        return store.get_charsets()[part_index]

    def setCharset(self, charset, part_index=0):
        """ See interfaces.IMailMessage
        """
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
        """ See interfaces.IMailMessage
        """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_content_type()
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_content_type()

    def setContentType(self, content_type, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_type(content_type)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_type(content_type)


    def getParams(self, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_params()
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_params()

    def getParam(self, param_name, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_param(param_name)
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_param(param_name)

    def setParam(self, param_name, param_value, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_param(param_name, param_value)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_param(param_name, param_value)

    def delParam(self, param_name, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.del_param(param_name)
        else:
            payload = store.get_payload()
            payload[part_index-1].del_param(param_name)

    def getHeader(self, name):
        """Get a message header.
        """
        store = self._getStore()
        return store[name]

    def setHeader(self, name, value):
        """Set a message header.
        """
        store = self._getStore()
        if store.has_key(name):
            # Erase previous header
            del store[name]
        store[name] = value

    def loadMessage(self, raw_msg):
        """ See interfaces.IMailMessage
        """
        ### XXX we'll do different load level here
        if self.cache_level == 0:
            # todo
            self._setStore(Message.Message())
        elif self.cache_level == 1:
            # todo fill headers
            self._setStore(Message.Message())
            store = self._getStore()
            for key in raw_msg.keys():
                store[key] = raw_msg[key]
        else:
            self._setStore(message_from_string(raw_msg))

    def getPersistentPartIds(self):
        """ retrieves a sequence of persistent parts
        """
        results = []
        i = 0
        for element in self.getParts():
            if element is not None:
                results.append(i)
            i += 1
        return results

InitializeClass(MailPart)

