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
import os

from zLOG import LOG, INFO, DEBUG
from OFS.Folder import Folder
from ZODB.PersistentMapping import PersistentMapping
from Globals import InitializeClass

from zope.interface import implements

from Products.ZCatalog.ZCatalog import ZCatalog
from Products.TextIndexNG2.TextIndexNG import TextIndexNG
from Products.TextIndexNG2.Stopwords import FileStopwords

from configuration import __file__ as landmark
from utils import makeId

stop_words_filename = os.path.join(os.path.dirname(landmark), 'stopwords.txt')

class MailStopWords(FileStopwords):
    pass

# one catalog per user
# has one index wich is 'TextIndexNG2"
class MailCatalog(ZCatalog):
    user_id = ''
    indexed_headers = ['Subject', 'To', 'From']
    index_body = 1

    def __init__(self, id, user_id='', title='', vocab_id=None, container=None):
        ZCatalog.__init__(self, id, title, vocab_id, container)
        self.user_id = user_id
        self.addIndex('searchable_text', 'TextIndexNG2')
        indexer = self.Indexes['searchable_text']
        # options, TODO : externalize as parameters
        indexer.indexed_fields = ['searchable_text']
        indexer.truncate_left = True
        indexer.use_parser = 'FrenchQueryParser'
        indexer.use_normalizer = 'french'
        indexer.use_stopwords =  MailStopWords(stop_words_filename)
        # we want power !
        indexer.splitter_separators =  ':'
        self.addColumn('id')
        self.addColumn('uid')
        self.addColumn('digest')

    def unIndexMessage(self, message):
        """ uncatalog an object
        """
        url = message.absolute_url()
        self.uncatalog_object(url)

    def indexMessage(self, message):
        """ index or reindex a mail content """
        # temporarely append searchable_content attribute to msg
        self.wrapMessage(message)
        try:
            self.catalog_object(message, message.absolute_url())
        finally:
            self.unWrapMessage(message)

    def wrapMessage(self, msg):
        """ wraps a message for indexation """
        searchable = []
        # indexing part of headers at this time
        indexed_headers = self.indexed_headers

        for indexed_header in indexed_headers:
            header_content = msg.getHeader(indexed_header)
            if header_content is not None:
                for element in header_content:
                    element_words = element.split(' ')
                    for word in element_words:
                        if word not in searchable:
                            searchable.append(word)

        # todo : index body even for message with cache_level = 1
        if self.index_body:
            body = msg.getDirectBody()
            if isinstance(body, str):
                words = body.split(' ')
            else:
                words = []

            searchable += words

        msg.searchable_text = ' '.join(searchable)

    def unWrapMessage(self, msg):
        """ suppress wrapper
        """
        msg.searchable_text = None

    def search(self, query_request, sort_index=None,
            reverse=0, limit=None, merge=1):
        """ search
        """
        # todo filter to supress duplicates
        return ZCatalog.search(self, query_request, sort_index,
            reverse, limit, merge)

InitializeClass(MailCatalog)
