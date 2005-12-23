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
    A message with a few more things for editor's view
"""
from email import Message
from cache.ram import RAMCache
from mailmessage import MailMessage

class MailEditorMessage(MailMessage):
    _cache = RAMCache()

    def __init__(self, id=None, uid='', digest='', **kw):
        MailMessage.__init__(self, id, uid, digest, **kw)
        self.answerType = ''
        self.origin_message = None
        self._setStore(Message.Message())

    def setCachedValue(self, name, value):
        name = {'key': name}
        self._cache.set(value, 'editor', name)

    def getCachedValue(self, name):
        name = {'key': name}
        return self._cache.query('editor', name)

    def loadFromMessage(self, msg):
        """ useful to adapt an existing message """
        self.copyFrom(msg)

    def setHeader(self, name, value):
        """ Set a message header. """
        store = self._getStore()
        while store.has_key(name):
            # Erase previous header
            del store[name]
        store[name] = value

