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
from zLOG import LOG, INFO

class BaseMailMessageView(BrowserView):

    def getIconName(self, short_title, selected):
        """ returns icon name
        """
        if short_title == 'Trash':
            return 'cpsma_trashcan.png'
        elif short_title == 'INBOX':
            return 'cpsma_mailbox.png'
        elif short_title == 'Drafts':
            return 'cpsma_draft.png'
        elif short_title == 'Sent':
            return 'cpsma_mailsent.png'
        else:
            if not selected:
                return 'cpsma_folder.png'
            else:
                return 'cpsma_folder_selected.png'

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
        ## XX add icon name
        for element in treeview:
            short_title = element['short_title']
            element['selected'] = element['object'] == selected
            element['icon_name'] = self.getIconName(short_title,
                element['selected'])
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

        level = 1

        parent_length = 1
        parent_index = 0

        if len(childs) > 0:
            ## should call interface instead here
            childview = BaseMailMessageView(None, self.request)
            index = 0
            length = len(childs)
            for child in childs:
                childview.context = child
                element = self.createTreeViewElement(child, firstfolder,
                    index, length, level, parent_index, parent_length)
                element['childs'] = childview._renderTreeView(firstfolder, level+1,
                    parent_index, parent_length, flags)
                treeview.append(element)
                index += 1

        mailbox.setTreeViewCache(treeview)

        return treeview

    def createTreeViewElement(self, element, selected_folder, index, length,
            level, parent_index, parent_length):
        """ creates a node for the tree
        """
        selected = element == selected_folder
        short_title = self.createShortTitle(element)
        icon_name = self.getIconName(short_title, selected)

        if element.childFoldersCount()==0:
            if index == 0 and length > 1:
                front_icons = [{'icon':'cma_center_empty.png', 'clickable' : False}]
            elif index == length - 1:
                front_icons = [{'icon':'cma_bottom_corner.png', 'clickable' : False}]
            else:
                front_icons = [{'icon':'cma_center_empty.png', 'clickable' : False}]
        else:
            if index == 0 and length >1 :
                front_icons = [{'icon':'cma_top_minus.png', 'clickable' : True}]
            elif index == 0:
                front_icons = [{'icon':'cma_minus.png', 'clickable' : True}]
            elif index == length - 1:
                front_icons = [{'icon':'cma_bottom_minus.png', 'clickable' : True}]
            else:
                front_icons = [{'icon':'cma_bottom_minus.png', 'clickable' : True}]

        for i in range(level-1):
            if self._hasParentNext(parent_index, parent_length):
                front_icons.insert(0, {'icon':'cma_center_line.png', 'clickable' : False})
            else:
                front_icons.insert(0, {'icon':'cma_empty.png', 'clickable' : False})

        short_title_id = short_title.replace(' ', '.')

        return {'object' :element,
                'level' : level,
                'url' :element.absolute_url()+'/view',
                'short_title' :short_title,
                'javacall' : 'switchFolderState("'+short_title_id+'")',
                'img_id' : 'img_' + short_title_id,
                'selected' : selected,
                'icon_name' : icon_name,
                'count' : length,
                'index' : index,
                'short_title_id' : short_title_id,
                'front_icons' : front_icons}

    def _hasParentNext(self, parent_index, parent_length):
        """ see if up level has some elements
        """
        return parent_index < parent_length -1



    def _renderTreeView(self, current, level, parent_index, parent_length,
            flags=[]):
        """ returns a tree view
            XXX need optimisation and cache use
        """
        treeview = []
        current_place = self.context
        childs = current_place.getMailMessages(list_folder=True, \
            list_messages=False, recursive=False)

        childview = BaseMailMessageView(None, self.request)
        index = 0
        length = len(childs)
        for child in childs:
            childview.context = child
            element = self.createTreeViewElement(child, current,
                index, length, level, parent_index, parent_length)
            element['childs'] = childview._renderTreeView(current, level+1,
                flags, length, index)
            treeview.append(element)
            index += 1

        return treeview
