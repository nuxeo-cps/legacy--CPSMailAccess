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
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.TextIndexNG2.TextIndexNG import TextIndexNG
from OFS.Folder import Folder
from Globals import InitializeClass
from zope.interface import implements
from UserDict import UserDict

# one catalog per user
# has one index wich is 'TextIndexNG2"

class MailCatalog(ZCatalog):
    user_id = ''
    searchable_text = TextIndexNG('searchable_text')

    def __init__(self, id, user_id='', title='', vocab_id=None, container=None):
        ZCatalog.__init__(self, id, title, vocab_id, container)
        self.user_id = user_id
        self.searchable_text.indexed_fields = ['searchable_content']

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
        msg.searchable_content = 'coucou ok jojo'

    def unWrapMessage(self, msg):
        msg.searchable_content = None


    def searchMessages(self, SearchText):
        """ searches a text into the catalog brains
            returns a list of msg urls
        """
        pass

InitializeClass(MailCatalog)

# catalog dictonnary
class MailCatalogDict(UserDict):

    def __init__(self, initlist=None):
        UserDict.__init__(self, initlist)

    def getCatalog(self, user_id):
        if self.has_key(user_id):
            return self[user_id]
        return None

    def addCatalog(self, user_id):
        if self.getCatalog(user_id) is None:
            self[user_id] = MailCatalog(user_id, user_id, user_id)

""" classic Zope 2 interface for class registering
"""
InitializeClass(MailCatalogDict)


