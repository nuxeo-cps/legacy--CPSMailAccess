# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
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
from Acquisition import aq_parent, aq_inner
from Products.Five import BrowserView
from Products.CPSMailAccess.mailexceptions import MailContainerError

class BaseMailMessageView(BrowserView):

    def createShortTitle(self, object):
        """ creates a short title
        """
        title = object.title
        titles = title.split('.')
        return titles[len(titles)-1]

    def setSelected(self, treeview, selected):
        """ sets selection
            XXX linear need optimisation
            this part used to refresh
            the selected folder
            makes the treeview cache
            not very useful
            selected folder should be found
            differently
        """
        for element in treeview:
            if element['object'] == selected:
                element['selected'] = True
            else:
                element['selected'] = False
            self.setSelected(element['childs'], selected)

    def renderTreeView(self, flags=[]):
        """ returns a tree view
            XXX need optimisation and cache use
        """
        mailbox = self.context.getMailBox()

        # XXX hack to avoid round import
        if hasattr(self.context, 'message_cache'):
            firstfolder = aq_parent(aq_inner(self.context))
        else:
            firstfolder = self.context

        if mailbox is None:
            raise MailContainerError('object is not contained in a mailbox')

        # let's check if the treeview has been already calculated
        treeview = mailbox.getTreeViewCache()

        if treeview is not None:
            self.setSelected(treeview, firstfolder)
            return treeview
        else:
            treeview = []

        childs = mailbox.getMailMessages(list_folder=True, \
            list_messages=False, recursive=False)

        if len(childs) > 0:
            childview = BaseMailMessageView(None, self.request)

            for child in childs:
                selected = child == firstfolder
                childview.context = child
                short_title = self.createShortTitle(child)
                treeview.append({'object' :child,
                                 'url' :child.absolute_url()+'/view',
                                 'short_title' :short_title,
                                 'selected' : selected,
                                 'childs' : childview._renderTreeView(firstfolder, flags)})

        mailbox.setTreeViewCache(treeview)

        return treeview

    def _renderTreeView(self, current, flags=[]):
        """ returns a tree view
            XXX need optimisation and cache use
        """
        treeview = []
        current_place = self.context
        childs = current_place.getMailMessages(list_folder=True, \
            list_messages=False, recursive=False)

        childview = BaseMailMessageView(None, self.request)

        for child in childs:
            childview.context = child
            short_title = self.createShortTitle(child)
            selected = child == current

            treeview.append({'object' :child,
                             'url' :child.absolute_url()+'/view',
                             'short_title' :short_title,
                             'selected' : selected,
                             'childs' : childview._renderTreeView(current, flags)})

        return treeview
