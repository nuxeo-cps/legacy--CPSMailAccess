# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
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
from ZODB.POSException import ReadConflictError
from Products.CPSMailAccess.interfaces import IMailBox, IMailMessage, \
                                              IMailFolder
from utils import translate
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
        success = False
        tries = 0
        while tries < 5 and not success:
            try:
                res = self._renderActions()
                success = True
            except ReadConflictError:
                tries += 1
        if success:
            return res
        else:
            return []

    def _renderActions(self):
        """ XXX need to use the mapping menuItems in CMFOnFive instead
            XX need to implements zope 3 action providers
        """
        root = ''
        container = self.context
        base_url = self.getBaseUrl()
        box = container.getMailBox()
        box_url = self.getAbsoluteUrl(box)

        if self._last_error is not None:
            root = self.getAbsoluteUrl(container)
            configure = {'icon' : base_url + '/cpsma_configure.png',
                         'title' : 'cpsma_configure',
                         'id' : 'configure',
                         'long_title' : 'cpsma_configure',
                         'action' : box_url + '/configure.html'}
            synchro = {'icon' : base_url + '/cpsma_getmails.png',
                       'title' : 'cpsma_getmessages',
                       'long_title' : 'cpsma_getmessages',
                       'id' : 'synchro',
                       'action' : box_url + \
                       '/syncProgress.html?light=1'}

            return [[synchro, configure]]

        actions = []

        if IMailBox.providedBy(container):
            root = self.getAbsoluteUrl(container)
            # are we in the editor ?
            if self.is_editor():
                save = {'icon' : base_url + '/cpsma_save.png',
                        'title' : 'cpsma_save_message',
                        'id' : 'save',
                        'long_title' : 'cpsma_save_message',
                        'onclick' : 'saveMessage()',
                        'action' : ''}

                """
                attach_file = {'icon' : base_url + '/cpsma_attach.png',
                     'title' : 'attach file',
                     'long_title' : 'add a file to the message',
                     'action' : 'editMessage.html?attach=1',
                     'onclick' : 'saveMessageDatas()'}

                """
                init = {'icon' : base_url + '/cpsma_initeditor.png',
                        'title' : 'cpsma_init_editor',
                        'long_title' : 'cpsma_init_editor',
                        'id' : 'init',
                        'action' : root + '/initializeEditor.html',
                        'onclick' : ''}


                send = {'icon' : base_url + '/cpsma_sendmsg.png',
                        'title' : 'send message',
                        'long_title' : 'cpsma_send_message',
                        'action' : '',
                        'id' : 'send',
                        'onclick' : 'sendMessage();'}

                ack = {'icon' : base_url + '/cpsma_ack.png',
                        'title' : 'cpsma_ack',
                        'long_title' : 'cpsma_ack',
                        'action' : '',
                        'id' : 'ack',
                        'onclick' : 'setAck();'}

                configure = {'icon' : base_url + '/cpsma_configure.png',
                             'title' : 'cpsma_configure',
                             'long_title' : 'cpsma_configure',
                             'id' : 'configure',
                             'action' : box_url + '/configure.html'}

                return [[send, save], [ack, init], [configure]]

        elif IMailFolder.providedBy(container):
            mailbox = container.getMailBox()
            root = self.getAbsoluteUrl(mailbox)
            candelete = (not mailbox.elementIsInTrash(container) and
                         not container.isReadOnly())
            confirm_msg = translate(mailbox, 'cpsma_confirm_erase')

            if container == mailbox.getTrashFolder():
                empty_trash = {'icon' : base_url + '/cpsma_emptytrash.png',
                               'title' : 'cpsma_empty_trash',
                               'long_title' : 'cpsma_empty_trash',
                               'id' : 'empty_trash',
                               'onclick' : "return window.confirm('%s')" % confirm_msg,
                               'action' : root + '/emptyTrash.html'}
                actions.append(empty_trash)

            elif container == mailbox.getDraftFolder():
                ##
                pass
            else:
                if container.canCreateSubFolder():

                    add_folder = {'icon' : base_url + '/cpsma_addfolder.png',
                                'title' : 'cpsma_add_subfolder',
                                'long_title' : 'cpsma_add_subfolder',
                                'action' : '',
                                'id' : 'add_folder',
                                'onclick' : "toggleElementVisibility('addFolder')"}
                    actions.append(add_folder)

                sent_server_name = mailbox.getSentFolder().server_name

                if container.server_name not in ('INBOX', sent_server_name):
                    move_folder = {'icon' : root + '/cpsma_movefolder.png',
                                   'title' : 'cpsma_move_folder',
                                   'long_title' : 'cpsma_move_folder',
                                   'action' : '',
                                   'id' : 'move_folder',
                                   'onclick' : "toggleElementVisibility('moveFolder')"
                                   }

                    rename = {'icon' : base_url + '/cpsma_rename.png',
                              'title' : 'cpsma_rename_folder',
                              'long_title' : 'cpsma_rename_folder',
                              'action' : '',
                              'id' : 'rename',
                              'onclick' : "toggleElementVisibility('renameFolder')"
                             }

                    if candelete:
                        confirm_msg = translate(mailbox, 'cpsma_confirm_erase_folder')

                        delete = {'icon' : base_url + '/cpsma_delete.png',
                                  'title' : 'cpsma_delete_folder',
                                  'long_title' : 'cpsma_delete_folder',
                                  'id' : 'delete',
                                  'onclick' : "return window.confirm('%s')" % confirm_msg,
                                  'action' : 'delete.html'}
                        list_ = [delete, rename, move_folder]
                    else:
                        list_ = [rename, move_folder]

                    actions.extend(list_)

            # XXX should test here if there's is filters for this folder
            if mailbox.hasFilters():
                filter_ = {'icon' : root + '/cpsma_filter_big.png',
                        'title' : 'cpsma_filter',
                        'long_title' : 'cpsma_filter',
                        'id' : 'filter',
                        'action' : 'runFilters.html'}
                actions.append(filter_)

            """
            removed (trac #13)
            manage = {'icon' : root + '/cpsma_manage_content.png',
                      'title' : 'cpsma_manage_content',
                      'long_title' : 'cpsma_manage_content',
                      'action' : 'view?manage_content=1&keep_last_sort=1'}
            actions.append(manage)
            """

        elif IMailMessage.providedBy(container):
            mailbox = container.getMailBox()
            root = self.getAbsoluteUrl(mailbox)

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
                         'title' : 'cpsma_reply',
                         'long_title' : 'cpsma_reply',
                         'id' : 'reply',
                         'action' : 'reply.html'}

                reply_all = {'icon' : base_url + '/cpsma_replyall.png',
                             'title' : 'cpsma_reply_all',
                             'long_title' : 'cpsma_reply_all',
                             'id' : 'reply_all',
                             'action' : 'replyAll.html'}

                actions.extend([reply, reply_all])


            if current_folder.id != trash_name:
                forward = {'icon' : base_url + '/cpsma_forward.png',
                           'title' : 'cpsma_forward',
                           'long_title' : 'cpsma_forward',
                           'id' : 'forward',
                           'action' : 'forward.html'}

                actions.append(forward)

            if (current_folder.id != trash_name and
                not current_folder.isReadOnly()):
                confirm_msg = translate(mailbox, 'cpsma_confirm_erase')
                delete = {'icon' : base_url + '/cpsma_delete.png',
                          'title' : 'cpsma_delete_message',
                          'long_title' : 'cpsma_delete_message',
                          'id' : 'delete_folder',
                          'onclick' : "return window.confirm('%s')" % confirm_msg,
                          'action' : 'delete.html'}

                actions.append(delete)

            if (current_folder.id == draft_name):
                draft = {'icon' : base_url + '/cpsma_reload.png',
                            'title' : 'cpsma_load_message',
                            'long_title' : 'cpsma_load_message',
                            'id' : 'draft',
                            'action' : 'reload.html'}
                actions.append(draft)
        else:
            return []

        configure = {'icon' : base_url + '/cpsma_configure.png',
                     'title' : 'cpsma_configure',
                     'long_title' : 'cpsma_configure',
                     'id' : 'configure',
                     'action' : box_url + '/configure.html'}

        synchro = {'icon' : base_url + '/cpsma_getmails.png',
                   'title' : 'cpsma_getmessages',
                   'long_title' : 'cpsma_getmessages',
                   'id' : 'synchro',
                   'action' : box_url + '/syncProgress.html?light=1'}

        search = {'icon' : base_url + '/cspma_mail_find.png',
                   'title' : 'cpsma_search_messages',
                   'long_title' : 'cpsma_search_messages',
                   'id' : 'search',
                   'action' : root + '/zemanticSearchMessage.html'}

        write   = {'icon' : base_url + '/cpsma_writemail.png',
                   'title' : 'cpsma_write_message',
                   'long_title' : 'cpsma_write_message',
                   'id' : 'write',
                   'action' : root + '/editMessage.html'}

        adressbook   = {'icon' : base_url + '/cpsma_addressbook.png',
                        'title' : 'cpsma_address_books',
                        'long_title' : 'cpsma_address_books',
                        'id' : 'adressbook',
                        'action' : root + '/addressBooks.html'}


        actions = [synchro, write, adressbook, search] + actions + [configure]
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
