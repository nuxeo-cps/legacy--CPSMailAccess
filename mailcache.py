# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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

from UserList import UserList
from zope.interface import implements
from Products.CPSMailAccess.interfaces import IMailMessageCache, IMailMessage
import thread

class MailCache(UserList):
    """ mailcache is a thread-safe list that holds temporarly messages
    >>> f = MailCache()
    >>> IMailMessageCache.providedBy(f)
    True
    """
    implements(IMailMessageCache)

    lock = thread.allocate_lock()

    def __init__(self, initlist=None):
        UserList.__init__(self, initlist)

    def retrieveMessage(self, msg_key, remove=False):
        """ see interface
        """
        self.lock.acquire()
        try:
            for message in self:
                if message.msg_key == msg_key:
                    if remove:
                        self.remove(message)
                    return message
            return None
        finally:
            self.lock.release()

    def putMessage(self, message):
        """ see interface
        """
        self.lock.acquire()
        try:
            if IMailMessage.providedBy(message):
                msg_key = message.msg_key
                found = False

                # we can't use retrieveMessage because of deadlock
                for cached_message in self:
                    if cached_message.msg_key == msg_key:
                        found = True
                        break

                if not found:
                    self.append(message)
                else:
                    raise Exception('%s already in the list' % message.msg_key)
            else:
                raise Exception('%s (%s) object has to implement IMailMessage' % (str(message),
                    message.getId()))
        finally:
            self.lock.release()

    def emptyList(self):
        """ see interface
        """
        for message in self:
            self.remove(message)
            del message

    def inCache(self, message):
        """ see interface
        """
        if IMailMessage.providedBy(message):
            msg = self.retrieveMessage(message.msg_key)
            return msg is not None
        return False