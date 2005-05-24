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
from utils import getToolByName, parseDateString, decodeHeader
from mailexceptions import MailCatalogError
from mailmessageview import MailMessageView

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

        dtime = time.time() - start
        return (results, dtime)

    def traverseToObject(self, path):
        """ transforms an url to its object """
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

    def zemanticPredicateList(self):
        """ retrieves all predicates """
        mailbox = self.context
        cat = mailbox._getZemanticCatalog()
        list_ = list(cat.uniquePredicates())
        list_.sort()
        return list_

    def _intersection(self, x, y):
        # in our case, intersection is made on subject
        result = []
        for e in x:
            for item in y:
                if e.triple()[0]  == item.triple()[0]:
                    result.append(e)
        return result

    def zemanticSearchMessages(self, **kw):
        """ zemantic query """
        start = time.time()
        mailbox = self.context
        i = 0
        found = True
        queries = []
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

                if value.strip() == '*':    # stands for all entries
                    query = Query(Any, u'<%s>' % relation, Any)
                else:
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
                    raw_results = self._intersection(query_results, raw_results)
                else:
                    raw_results = query_results

                i += 1
                if raw_results == []:
                    break

        if raw_results == [None]:
            raw_results = []
        else:
            raw_results = [raw_result.triple()[0] \
                           for raw_result in raw_results]

        results = []
        msg_viewer = MailMessageView(None, self.request)
        for result in raw_results:
            object = self.traverseToObject(result)
            # if object is None, it means
            # that the catalog holds deprecated entries
            # we don't want to see here
            if object is not None:
                current = {}
                current['path'] = result
                current['object'] = object
                # see if this can be done more quickly
                msg_viewer.context = object
                current['From'] = msg_viewer.renderFromList()
                current['Subject'] = msg_viewer.renderSubject()
                current['Date'] = msg_viewer.renderDate()
                # always sorting by date
                element_date = object.getHeader('Date')
                if element_date is None or element_date == []:
                    element_date = '?'
                stDate = decodeHeader(element_date[0])
                sorter = parseDateString(stDate)
                results.append((sorter, current))

        results.sort()
        results.reverse()

        sorted_results = [result[1] for result in results]

        dtime = time.time() - start
        return (sorted_results, dtime, len(cat))
