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
# $Id$

from Products.Five import BrowserView
from utils import getToolByName

class MailSearchView(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def _getCatalog(self, user_id):
        """ retrieves the right catalog
        """
        mailtool = getToolByName(self.context, 'portal_webmail')
        cat = mailtool.mail_catalogs
        return cat.getCatalog(user_id)

    def search(self, user_id, searchable_text):
        """ search the catalog
        """
        results = []
        cat = self._getCatalog(user_id)
        if cat is not None:
            query = {}
            query['searchable_text'] = searchable_text
            raw_results = cat.search(query_request=query)
            for result in raw_results:
                ob = result.getObject()
                results.append(ob)
        return results

