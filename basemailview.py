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
from zLOG import LOG, INFO
from Acquisition import aq_parent, aq_inner
from Products.Five import BrowserView

from interfaces import IMailMessage
from utils import getToolByName
from mailexceptions import MailContainerError

class BaseMailMessageView(BrowserView):

    def getBaseUrl(self):
        portal_url = getToolByName(self.context, 'portal_url')
        return portal_url.getPortalPath()     # check if ok behind apache

    def getIconName(self, short_title, selected, root):
        """Return icon name
        """
        if short_title == 'Trash':
            return root + '/cpsma_trashcan.png'
        elif short_title == 'INBOX':
            return root + '/cpsma_mailbox.png'
        elif short_title == 'Drafts':
            return root + '/cpsma_draft.png'
        elif short_title == 'Sent':
            return root + '/cpsma_mailsent.png'
        else:
            if not selected:
                return root + '/cpsma_folder.png'
            else:
                return root + '/cpsma_folder_selected.png'

    def createShortTitle(self, object):
        """Create a short title
        """
        title = object.title
        if title is None or title == '':
            return ''
        titles = title.split('.')
        return titles[len(titles)-1]

    def _setSelected(self, treeview, selected, root):
        """Set selection

           XXX linear need optimisation
           this part used to refresh the selected folder makes the treeview
           cache not very useful
           selected folder should be found differently
        """
        ## XX add icon name
        for element in treeview:
            short_title = element['short_title']
            element['selected'] = element['object'] == selected
            element['icon_name'] = self.getIconName(short_title,
                element['selected'], root)
            self._setSelected(element['childs'], selected, root)

    def renderTreeView(self, flags=[]):
        """Return a tree view

           XXX need optimisation and cache use
        """
        mailbox = self.context.getMailBox()
        mailbox.clearTreeViewCache()

        portal_url = getToolByName(mailbox, 'portal_url')
        base_url = portal_url.getPortalPath()


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
            self._setSelected(treeview, firstfolder, base_url)
            return treeview
        else:
            treeview = []

        childs = mailbox.getMailMessages(list_folder=True,
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
                element = self._createTreeViewElement(child, firstfolder,
                    index, length, level, parent_index, parent_length, base_url)
                unreads, element['childs'] = childview._renderTreeView(firstfolder, level+1,
                    parent_index, parent_length, base_url, flags)
                element['unreads'] = unreads
                treeview.append(element)
                index += 1

        mailbox.setTreeViewCache(treeview)

        return treeview

    def _createTreeViewElement(self, element, selected_folder, index, length,
            level, parent_index, parent_length, root):
        """Create a node for the tree
        """
        selected = (element == selected_folder)
        short_title = self.createShortTitle(element)
        icon_name = self.getIconName(short_title, selected, root)

        if element.childFoldersCount() == 0:
            if index == 0 and length > 1:
                front_icons = [{'icon': root + '/cma_center_empty.png',
                                'clickable': False}]
            elif index == length - 1:
                front_icons = [{'icon': root + '/cma_bottom_corner.png',
                                'clickable': False}]
            else:
                front_icons = [{'icon': root + '/cma_center_empty.png',
                                'clickable': False}]
        else:

            if index == 0 and length >1 :
                front_icons = [{'icon': root + '/cma_top_minus.png',
                                'clickable': True}]
            elif index == 0:
                front_icons = [{'icon': root + '/cma_minus.png',
                                'clickable': True}]
            elif index == length - 1:
                front_icons = [{'icon': root + '/cma_bottom_minus.png',
                                'clickable': True}]
            else:
                front_icons = [{'icon': root + '/cma_bottom_minus.png',
                                'clickable': True}]

        for i in range(level-1):
            if self._hasParentNext(parent_index, parent_length):
                """ commented out (alog need review)
                front_icons.insert(0, {'icon': root + '/cma_center_line.png',
                                       'clickable' : False})
                """
                front_icons.insert(0, {'icon': root + '/cma_empty.png',
                                       'clickable' : False})
            else:
                front_icons.insert(0, {'icon': root + '/cma_empty.png',
                                       'clickable': False})

        short_title_id = short_title.replace(' ', '.')

        # todo : see for localhost problems here
        # all this is done due to python interpreting problems
        # (should be ok when Five is merged with support Z2 page templates)
        url = element.absolute_url()

        rename_url = 'rename?fullname=1&new_name=%s.%s' % (element.server_name,
            selected_folder.simpleFolderName())

        not_for_move = element.id == selected_folder.id or \
            element.getMailFolder().id == selected_folder.id or  \
            element.id in ('Trash', 'Sent', 'Drafts')

        return {'object': element,
                'level': level,
                'url': url +'/view',
                'short_title': short_title,
                'javacall': 'switchFolderState("'+short_title_id+'")',
                'img_id': 'img_' + short_title_id,
                'selected': selected,
                'icon_name': icon_name,
                'count': length,
                'index': index,
                'server_name': element.server_name,
                'rename_url': rename_url,
                'short_title_id': short_title_id,
                'not_for_move': not_for_move,
                'front_icons': front_icons}

    def _hasParentNext(self, parent_index, parent_length):
        """See if up level has some elements
        """
        return parent_index < parent_length -1

    def _renderTreeView(self, current, level, parent_index, parent_length,
                        root, flags=[]):
        """Return a tree view

           XXX need optimisation and cache use
        """
        treeview = []
        current_place = self.context
        childs = current_place.getMailMessages(list_folder=True,
            list_messages=False, recursive=False)

        childview = BaseMailMessageView(None, self.request)
        index = 0
        unreads = 0
        length = len(childs)
        for child in childs:
            childview.context = child
            element = self._createTreeViewElement(child, current,
                index, length, level, parent_index, parent_length, root)
            if hasattr(element, 'getFlaggedMessageList'):
                # todo : a finir
                list = element.getFlaggedMessageList(['read'])
                unreads += len(list)

            unreads, element['childs'] = childview._renderTreeView(current, level+1,
                index, length, root, flags)
            element['unreads'] =  unreads
            treeview.append(element)
            index += 1

        # sort the treeview
        stree = []
        for element in treeview:
            if element['short_title'] == 'Sent':
                stree.append((1, element))
            elif element['short_title'] == 'Drafts':
                stree.append((0, element))
            elif element['short_title'] == 'Trash':
                stree.append((2, element))
            else:
                stree.append((element['short_title'], element))
        stree.sort()
        ntreeview = []
        for element in stree:
            ntreeview.append(element[1])

        return unreads, ntreeview
