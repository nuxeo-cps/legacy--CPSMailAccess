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
from Products.CPSMailAccess.interfaces import IMailBox, IMailMessage, IMailFolder
from Products.Five import BrowserView

""" XXXX using a view to retrieve actions
    to avoid the use of portal_actions
    in the rendering process

    *** this has to be refactored
    using the proper action provider mechanism  under five/zope3
"""
class MailActionsView(BrowserView):

    def is_editor(self):
        """ tells if we are in editor view (hack)
        """
        if self.request is not None:
            url_elements = self.request['URL'].split('/')
            len_url = len(url_elements)
            return url_elements[len_url-1]=='editMessage.html'
        else:
            return False

    def renderActions(self):
        """ XXX need to use the mapping menuItems in CMFOnFive instead
            XX need to implements zope 3 action providers
        """
        container = self.context
        actions = []

        if IMailBox.providedBy(container):
            root = container.absolute_url()
            # are we in the editor ?
            if self.is_editor():
                save = {'icon' : 'cpsma_save.png',
                     'title' : 'save message',
                     'long_title' : 'save the message in Drafts',
                     'onclick' : 'saveMessageDatas()',
                     'action' : 'save'}

                attach_file = {'icon' : 'cpsma_attach.png',
                     'title' : 'attach file',
                     'long_title' : 'add a file to the message',
                     'action' : 'editMessage.html?attach=1',
                     'onclick' : 'saveMessageDatas()'}

                send = {'icon' : 'cpsma_sendmsg.png',
                                 'title' : 'send message',
                                 'long_title' : 'send the message',
                                 'action' : 'editMessage.html',
                                 'onclick' : 'saveMessageDatas();alert("click below");'}

                return [[save, attach_file], [send]]

        elif IMailFolder.providedBy(container):
            mailbox = container.getMailBox()
            root = mailbox.absolute_url()

            if container == mailbox.getTrashFolder():
                empty_trash = {'icon' : 'cpsma_emptytrash.png',
                               'title' : 'empty trash',
                               'long_title' : 'empty the trashcan',
                               'onclick' : "return window.confirm('Are you sure?')",
                               'action' : 'emptyTrash'}
                actions.append(empty_trash)

            elif container == mailbox.getDraftFolder():
                pass
            elif container == mailbox.getSentFolder():
                pass
            else:
                add_folder = {'icon' : 'cpsma_addfolder.png',
                            'title' : 'add subfolder',
                            'long_title' : 'add a subfolder',
                            'action' : 'view?add_folder=1'}
                actions.append(add_folder)

                if container.server_name != 'INBOX':
                    move_folder = {'icon' : 'cpsma_movefolder.png',
                            'title' : 'move folder',
                            'long_title' : 'move the folder',
                            'action' : 'view?move_folder=1'}
                    delete = {'icon' : 'cpsma_delete.png',
                                'title' : 'delete folder',
                                'long_title' : 'delete current folder',
                                'onclick' : "return window.confirm('Are you sure?')",
                                'action' : 'delete'}
                    rename = {'icon' : 'cpsma_rename.png',
                                'title' : 'rename folder',
                                'long_title' : 'rename current folder',
                                'action' : 'view?edit_name=1'}
                    actions.extend([delete, rename, move_folder])

            manage = {'icon' : 'cpsma_manage_content.png',
                'title' : 'manage content',
                'long_title' : 'manage current folder',
                'action' : 'view?manage_content=1'}
            actions.append(manage)

        elif IMailMessage.providedBy(container):
            root = container.getMailBox().absolute_url()

            reply = {'icon' : 'cpsma_reply.png',
                     'title' : 'reply',
                     'long_title' : 'reply to message',
                     'action' : 'reply'}

            reply_all = {'icon' : 'cpsma_replyall.png',
                     'title' : 'reply all',
                     'long_title' : 'reply to message (all)',
                     'action' : 'reply_all'}

            forward = {'icon' : 'cpsma_forward.png',
                     'title' : 'forward',
                     'long_title' : 'forward the message',
                     'action' : 'forward'}

            delete = {'icon' : 'cpsma_delete.png',
                     'title' : 'delete message',
                     'long_title' : 'delete the message',
                     'onclick' : "return window.confirm('Are you sure?')",
                     'action' : 'delete'}

            actions.extend([reply, reply_all, forward, delete])

        else:
            return []

        configure = {'icon' : 'cpsma_configure.png',
                     'title' : 'configure',
                     'long_title' : 'configure the webmail',
                     'action' : root + '/configure.html'}
        synchro = {'icon' : 'cpsma_getmails.png',
                   'title' : 'get messages',
                   'long_title' : 'get all messages',
                   'action' : root + '/synchronize'}

        search = {'icon' : 'cspma_mail_find.png',
                   'title' : 'search messages',
                   'long_title' : 'searchin messages',
                   'action' : root + '/searchMessage.html'}

        write   = {'icon' : 'cpsma_writemail.png',
                   'title' : 'write message',
                   'long_title' : 'write a message',
                   'action' : root + '/editMessage.html'}

        actions = [configure, synchro, search, write] + actions
        # renders actions 2 by 2
        c_actions = []
        i = 0
        while i < len(actions):
            if i+1<len(actions):
                c_actions.append([actions[i], actions[i+1]])
            else:
                c_actions.append([actions[i]])
            i+=2
        return c_actions
