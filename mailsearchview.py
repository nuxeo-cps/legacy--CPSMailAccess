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
import os
import time

from Products.Five import BrowserView
from utils import getToolByName, parseDateString, decodeHeader, getFolder, \
                  traverseToObject
from mailexceptions import MailCatalogError
from mailmessageview import MailMessageView
from mailsearch import intersection  as z_intersection
from mailsearch import unifyList as z_unifyList

# XXXX todo: outsource ALL zemantic related stuff into mailsearch
from zemantic.public import *
from zemantic.query import UnionChain

class MailSearchView(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def searchMessages(self, searchable_text):
        """ search the catalog """
        start = time.time()
        # XXX encoding in iso8859-15 (today's CPS)
        searchable_text = searchable_text.strip().decode('ISO-8859-15')
        if searchable_text == '':
            return []
        box = self.context
        user_id = box.getConnectionParams()['uid']
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
                object = traverseToObject(box, current['path'])
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

        dtime = time.time() - start
        return (results, dtime)

    def zemanticPredicateList(self):
        """ retrieves all predicates """
        mailbox = self.context
        cat = mailbox._getZemanticCatalog()
        list_ = list(cat.uniquePredicates())
        list_.sort()
        return list_

    def _bodySearch(self, query):
        """ makes an IMAP search and translate UIDS results in URIS """
        mailbox = self.context
        results = mailbox.searchInConnection('(body "%s")' % query)
        uris = []
        for server_res in results:
            server_folder = server_res[0]
            server_uids = server_res[1]
            server_ob = getFolder(mailbox, server_folder)
            if server_ob is not None:
                for uid in server_uids:
                    # uids are given in a tuple (server_dir, uid)
                    ob = server_ob.findMessageByUid(uid)
                    if ob is not None:
                        uris.append(ob.absolute_url())
            return uris

    def zemanticSearchMessages(self, **kw):
        """ zemantic query """
        start = time.time()
        mailbox = self.context
        i = 0
        body_search = False
        body_search_query = None
        queries = []
        numparam = 0
        # maximum parameters == kw length / 2
        while i < len(kw.keys()) / 2:
            rrelation = 'relation_%d' %  i
            rvalue = 'value_%d' %  i
            # increment here because of continue statement
            i += 1
            if kw.has_key(rrelation) and kw.has_key(rvalue):
                value = kw[rvalue].lower()

                if value.strip() == '':    # we skip empty value
                    continue

                relation = kw[rrelation]

                # XXX encoding in iso8859-15 (today's CPS)
                if not isinstance(relation, unicode):
                    relation = relation.strip().decode('ISO-8859-15')
                relation = relation.lower()
                value = value.strip()

                if relation == 'body':
                    # special case: mail body is not indexed by zope
                    body_search = True
                    body_search_query = value
                else:
                    numparam += 1
                    if len(value) == 1 and value in '?*':    # stands for all entries
                        # XXX need to be outsourced in mailsearch
                        query = Query(Any, u'<%s>' % relation, Any)
                    else:
                        if len(value) > 1 and value[0] in '?*':
                            value[0] = '_'
                        if not isinstance(value, unicode):
                            value = value.strip().decode('ISO-8859-15')
                        query = Query(Any, u'<%s>' % relation, u'"%s"' % value)
                    queries.append(query)

        cat = mailbox._getZemanticCatalog()

        intersection = kw.has_key('intersection')

        if not intersection:
            # joining queries with an or statement
            union = UnionChain()
            for query in queries:
                union.add(query)
            raw_results = cat.query(union)
            raw_results = list(raw_results)
        else:
            # doing queries one by one
            # and intersect them one by one
            # if the interesection gets empty we can stop
            i = 0
            raw_results = []

            for query in queries:
                query_results = cat.query(query)
                query_results = list(query_results)

                if query_results == [None]:
                    query_results = []

                if i > 0:
                    raw_results = z_intersection(query_results, raw_results)
                else:
                    raw_results = query_results

                i += 1
                if raw_results == []:
                    break

        if raw_results == [None]:
            raw_results = []
        else:
            raw_results = z_unifyList(raw_results)

        # after zemantic has done its works,
        # we might sub-search bodies on IMAP
        if body_search:
            body_search_results = self._bodySearch(body_search_query)
            if not intersection:
                raw_results.append(body_search_results)
            else:
                if raw_results != []:
                    raw_results = z_intersection(body_search_results,
                                                 raw_results)
                else:
                    # one intersection
                    if numparam == 0:
                        raw_results = body_search_results

        results = []
        msg_viewer = MailMessageView(None, self.request)
        for result in raw_results:
            object = traverseToObject(mailbox, result)
            # if object is None, it means
            # that the catalog holds deprecated entries
            # we don't want to see here
            if object is not None or kw.has_key('lazy_search'):
                current = {}
                current['path'] = result
                current['object'] = object
                # see if this can be done more quickly
                msg_viewer.context = object
                current['From'] = msg_viewer.renderFromList()
                current['Subject'] = msg_viewer.renderSubject()
                current['Date'] = msg_viewer.renderDate()
                # always sorting by date
                if object is not None:
                    element_date = object.getHeader('Date')
                    if element_date is None or element_date == []:
                        element_date = '?'
                    stDate = decodeHeader(element_date[0])
                    sorter = parseDateString(stDate)
                else:
                    sorter = 0
                results.append((sorter, current))

        results.sort()
        results.reverse()

        # XXX at this time, no batch, limit the result to 100 entries
        if len(results) > 100:
            results = results[:100]

        sorted_results = [result[1] for result in results]

        dtime = time.time() - start
        return (sorted_results, dtime, len(cat))
