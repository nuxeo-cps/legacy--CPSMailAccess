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

import thread
from zope.interface import implements

from Products.CPSMailAccess.interfaces import IMailMessageCache, IMailMessage


class MailCache(object):
    """MailCache

    This is a thread-safe datastructure that holds temporary messages.

    >>> f = MailCache()
    >>> IMailMessageCache.providedBy(f)
    True
    """
    implements(IMailMessageCache)

    lock = thread.allocate_lock()

    def __init__(self):
        self.clear()

    def clear(self):
        """See IMailMessageCache.
        """
        self.lock.acquire()
        try:
            self.cache = {}
        finally:
            self.lock.release()

    def get(self, digest, default=None, remove=False):
        """See IMailMessageCache.
        """
        self.lock.acquire()
        try:
            message = self.cache.get(digest, default)
            if remove and self.cache.has_key(digest):
                del self.cache[digest]
            return message
        finally:
            self.lock.release()

    def __getitem__(self, digest):
        """See IMailMessageCache.
        """
        return self.get(digest)

    def __setitem__(self, digest, message):
        """See IMailMessageCache.
        """
        self.lock.acquire()
        try:
            self.cache[digest] = message
        finally:
            self.lock.release()

    def has_key(self, digest):
        """See IMailMessageCache.
        """
        self.lock.acquire()
        try:
            return self.cache.has_key(digest)
        finally:
            self.lock.release()

    def __len__(self):
        """See IMailMessageCache.
        """
        self.lock.acquire()
        try:
            return len(self.cache)
        finally:
            self.lock.release()
