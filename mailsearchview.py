# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziad� <tz@nuxeo.com>
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

from Products.Five import BrowserView
from utils import getToolByName
from mailexceptions import MailCatalogError
from mailmessageview import MailMessageView

class MailSearchView(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def searchMessages(self, searchable_text):
        """ search the catalog
        """
        # XXX encoding in iso8859-15 (today's CPS)
        searchable_text = searchable_text.strip().decode('ISO-8859-15')
        if searchable_text == '':
            return []
        box = self.context
        user_id = box.connection_params['uid']
        results = []
        cat = box._getCatalog()
        msg_viewer = MailMessageView(None, self.request)

        if cat is not None:
            query = {}
            query['searchable_text'] = searchable_text
            raw_results = cat.search(query_request=query)
            for result in raw_results:
                current = {}
                current['path'] = result.getPath()
                object = self.traverseToObject(current['path'])
                current['object'] = object
                current['rid'] = result.getRID()
                # see if this can be done more quickly
                msg_viewer.context = object
                current['From'] = msg_viewer.renderFromList()
                current['Subject'] = msg_viewer.renderSubject()
                current['Date'] = msg_viewer.renderDate()

                results.append(current)
        else:
            raise MailCatalogError('No catalog for %s' % user_id)
        return results

    def traverseToObject(self, path):
        """ transforms an url to its object
        """
        # XXX needs refactoring
        mailbox = self.context
        path = path.split('/')
        if len(path) == 0:
            return None
        while len(path) > 0 and path[0] != mailbox.id:
            del path[0]
        if len(path) == 0:
            return None
        # starting at mailbox
        del path[0]
        subject = mailbox
        for element in path:
            if hasattr(subject, element):
                subject = getattr(subject, element)
            else:
                return None
        return subject

