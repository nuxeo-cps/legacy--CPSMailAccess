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
from Products.CPSMailAccess.interfaces import IMailBox, IMailMessage, \
    IMailFolder
from Products.Five import BrowserView

from utils import getToolByName
from basemailview import BaseMailMessageView

""" XXXX using a view to retrieve actions
    to avoid the use of portal_actions
    in the rendering process

    *** this has to be refactored
    using the proper action provider mechanism  under five/zope3
"""
class MailActionsView(BaseMailMessageView):

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
        base_url = self.getBaseUrl()

        if IMailBox.providedBy(container):
            root = container.absolute_url()

            # are we in the editor ?
            if self.is_editor():
                save = {'icon' : base_url + '/cpsma_save.png',
                     'title' : 'save message',
                     'long_title' : 'save the message in Drafts',
                     'onclick' : 'saveMessageDatas()',
                     'action' : 'saveMessage.html'}

                """
                attach_file = {'icon' : base_url + '/cpsma_attach.png',
                     'title' : 'attach file',
                     'long_title' : 'add a file to the message',
                     'action' : 'editMessage.html?attach=1',
                     'onclick' : 'saveMessageDatas()'}

                """
                init = {'icon' : base_url + '/cpsma_initeditor.png',
                     'title' : 'init editor',
                     'long_title' : 'initialize editor',
                     'action' : 'initializeEditor.html',
                     'onclick' : ''}

                """
                send = {'icon' : base_url + '/cpsma_sendmsg.png',
                                 'title' : 'send message',
                                 'long_title' : 'send the message',
                                 'action' : 'editMessage.html',
                                 'onclick' : 'saveMessageDatas();alert("click below");'}
                """

                return [[save, init]]

        elif IMailFolder.providedBy(container):
            mailbox = container.getMailBox()
            root = mailbox.absolute_url()
            candelete = not mailbox.elementIsInTrash(container)

            if container == mailbox.getTrashFolder():
                empty_trash = {'icon' : base_url + '/cpsma_emptytrash.png',
                               'title' : 'empty trash',
                               'long_title' : 'empty the trashcan',
                               'onclick' : "return window.confirm('Are you sure?')",
                               'action' : root + '/emptyTrash.html'}
                actions.append(empty_trash)

            elif container == mailbox.getDraftFolder():
                pass
            elif container == mailbox.getSentFolder():
                pass
            else:
                if container.canCreateSubFolder():

                    add_folder = {'icon' : base_url + '/cpsma_addfolder.png',
                                'title' : 'add subfolder',
                                'long_title' : 'add a subfolder',
                                'action' : 'view?add_folder=1'}
                    actions.append(add_folder)

                if container.server_name != 'INBOX':
                    move_folder = {'icon' : root + '/cpsma_movefolder.png',
                                   'title' : 'move folder',
                                   'long_title' : 'move the folder',
                                   'action' : 'view?move_folder=1'}
                    rename = {'icon' : base_url + '/cpsma_rename.png',
                                'title' : 'rename folder',
                                'long_title' : 'rename current folder',
                                'action' : 'view?edit_name=1'}

                    if candelete:
                        delete = {'icon' : base_url + '/cpsma_delete.png',
                                    'title' : 'delete folder',
                                    'long_title' : 'delete current folder',
                                    'onclick' : "return window.confirm('Are you sure?')",
                                    'action' : 'delete.html'}
                        list_ = [delete, rename, move_folder]
                    else:
                        list_ = [rename, move_folder]

                    actions.extend(list_)

            manage = {'icon' : root + '/cpsma_manage_content.png',
                      'title' : 'manage content',
                      'long_title' : 'manage current folder',
                      'action' : 'view?manage_content=1'}
            actions.append(manage)

        elif IMailMessage.providedBy(container):
            mailbox = container.getMailBox()
            root = mailbox.absolute_url()

            trash_name = mailbox.getTrashFolderName().split('.')[-1]
            draft_name = mailbox.getDraftFolderName().split('.')[-1]
            sent_name = mailbox.getSentFolderName().split('.')[-1]

            current_folder = container.getMailFolder()
            special_folder = False

            if current_folder is not None:
                if current_folder.id in (trash_name, sent_name, draft_name):
                    special_folder = True

            if not special_folder:
                reply = {'icon' : base_url + '/cpsma_reply.png',
                        'title' : 'reply',
                        'long_title' : 'reply to message',
                        'action' : 'reply.html'}

                reply_all = {'icon' : base_url + '/cpsma_replyall.png',
                        'title' : 'reply all',
                        'long_title' : 'reply to message (all)',
                        'action' : 'replyAll.html'}

                forward = {'icon' : base_url + '/cpsma_forward.png',
                        'title' : 'forward',
                        'long_title' : 'forward the message',
                        'action' : 'forward.html'}

                actions.extend([reply, reply_all, forward])

                if container.draft:
                    draft = {'icon' : base_url + '/cpsma_reload.png',
                        'title' : 'load message',
                        'long_title' : 'load the message into the editor',
                        'action' : 'reload.html'}
                    actions.extend([draft])


            if current_folder.id != trash_name:
                delete = {'icon' : base_url + '/cpsma_delete.png',
                        'title' : 'delete message',
                        'long_title' : 'delete the message',
                        'onclick' : "return window.confirm('Are you sure?')",
                        'action' : 'delete.html'}

                actions.append(delete)

        else:
            return []

        configure = {'icon' : base_url + '/cpsma_configure.png',
                     'title' : 'configure',
                     'long_title' : 'configure the webmail',
                     'action' : root + '/configure.html'}
        synchro = {'icon' : base_url + '/cpsma_getmails.png',
                   'title' : 'get messages',
                   'long_title' : 'get all messages',
                   'action' : root + '/syncProgress.html'}

        search = {'icon' : base_url + '/cspma_mail_find.png',
                   'title' : 'search messages',
                   'long_title' : 'searchin messages',
                   'action' : root + '/zemanticSearchMessage.html'}

        write   = {'icon' : base_url + '/cpsma_writemail.png',
                   'title' : 'write message',
                   'long_title' : 'write a message',
                   'action' : root + '/editMessage.html'}

        adressbook   = {'icon' : base_url + '/cpsma_addressbook.png',
                        'title' : 'address books',
                        'long_title' : 'address books',
                        'action' : root + '/addressBooks.html'}


        actions = [configure, synchro, search, write, adressbook] + actions
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
