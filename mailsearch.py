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
"""
  mailsearch holds all mail searches
"""
from zLOG import LOG, INFO, DEBUG
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.TextIndexNG2.TextIndexNG import TextIndexNG
"""
important TODO : use zope 3 catalog here, that is available on zope 3 cvs
          http://svn.zope.org/Zope3/trunk/src/zope/app/catalog/
          TODO 2 : make an optinal body parsing
"""
from OFS.Folder import Folder
from ZODB.PersistentMapping import PersistentMapping

from Globals import InitializeClass
from zope.interface import implements
from utils import makeId

# one catalog per user
# has one index wich is 'TextIndexNG2"
class MailCatalog(ZCatalog):
    user_id = ''
    indexed_headers = ['Subject', 'To', 'From']
    stop_list = ['com', 'net', 'org', 'fr']
    _v_cached_search = PersistentMapping()

    def __init__(self, id, user_id='', title='', vocab_id=None, container=None):
        ZCatalog.__init__(self, id, title, vocab_id, container)
        self.user_id = user_id
        self.addIndex('searchable_text', 'TextIndexNG')
        self.Indexes['searchable_text'].indexed_fields = ['searchable_text']
        self.addColumn('id')
        self.addColumn('uid')
        self.addColumn('digest')

    def unIndexMessage(self, message):
        """ uncatalog an object
        """
        url = message.absolute_url()
        self.uncatalog_object(url)

    def indexMessage(self, message):
        """ index or reindex a mail content
        """
        # temporarely append searchable_content attribute to msg
        self.wrapMessage(message)
        try:
            self.catalog_object(message, message.absolute_url())
        finally:
            self.unWrapMessage(message)

    def wrapMessage(self, msg):
        """ wraps a message for indexation
        """
        searchable = []
        # indexing part of headers at this time
        indexed_headers = self.indexed_headers
        stop_list = self.stop_list

        for indexed_header in indexed_headers:
            header_content = msg.getHeader(indexed_header)
            if header_content is not None:
                for element in header_content:
                    element_words = element.split(' ')
                    for word in element_words:
                        if word not in searchable and word not in stop_list:
                            searchable.append(word)

        msg.searchable_text = ' '.join(searchable)

    def unWrapMessage(self, msg):
        """ suppress wrapper
        """
        msg.searchable_text = None

    def _makeKey(self, query_request, sort_index, reverse, limit, merge):
        """ create search key
        """
        search_key = str(query_request) + '___' + str(sort_index) + \
             '___' + str(reverse) + '___' + str(limit) + \
             '___' + str(merge)
        return search_key

    def search(self, query_request, sort_index=None,
        reverse=0, limit=None, merge=1):
        """ speeding up things by caching searches
        """
        key = self._makeKey(query_request, sort_index, reverse, limit, merge)

        if self._v_cached_search.has_key(key):
            return self._v_cached_search[key]
        else:
            results = ZCatalog.search(self, query_request, sort_index,
                reverse, limit, merge)

            self._v_cached_search[key] = results
            return results

InitializeClass(MailCatalog)

# catalog dictonnary
class MailCatalogDict(Folder):
    def __init__(self):
        Folder.__init__(self)

    def getCatalog(self, user_id):
        user_id = makeId(user_id)
        if hasattr(self, user_id):
            return getattr(self, user_id)
        return None

    def addCatalog(self, user_id):
        user_id = makeId(user_id)
        if not hasattr(self, user_id):
            catalog = MailCatalog(user_id, user_id, user_id)
            self._setObject(user_id, catalog)

""" classic Zope 2 interface for class registering
"""
InitializeClass(MailCatalogDict)


