# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziadé <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# # it under the terms of the GNU General Public License version 2 as published
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
from math import ceil

from zLOG import LOG, INFO, DEBUG

from zope.app.cache.ram import RAMCache
from zope.interface import directlyProvides, directlyProvidedBy

from basemailview import BaseMailMessageView
from baseconnection import ConnectionError
from interfaces import IMailMessage, ITrashFolder, IDraftFolder, ISentFolder,\
                       IContainerFolder
from utils import *

class MailFolderView(BaseMailMessageView):

    def __init__(self, context, request):
        BaseMailMessageView.__init__(self, context, request)
        # marking folder
        context = self.context
        if context is not None:
            if self._last_error is None:
                self._setMarkers(context)

    def _setMarkers(self, context):
        """ setting up markers """
        box = context.getMailBox()
        if box is not None:
            if context == box.getTrashFolder():
                directlyProvides(context, (ITrashFolder) + \
                                directlyProvidedBy(context))
            elif context == box.getDraftFolder():
                directlyProvides(context, (IDraftFolder) + \
                                directlyProvidedBy(context))
            elif context == box.getSentFolder():
                directlyProvides(context, (ISentFolder) + \
                                directlyProvidedBy(context))
            if context.canCreateSubFolder():
                directlyProvides(context, (IContainerFolder) + \
                                directlyProvidedBy(context))

    def getMaxFolderSize(self):
        mailfolder = self.context
        mailbox = mailfolder.getMailBox()
        return int(mailbox.getConnectionParams()['max_folder_size'])

    def rename(self, new_name):
        """ action called to rename the current folder """
        mailfolder = self.context
        mailbox = mailfolder.getMailBox()
        max_folder_size = self.getMaxFolderSize()
        if len(new_name) > max_folder_size:
            new_name = new_name[:max_folder_size]

        if mailfolder.title == new_name:
            if self.request is not None:
                self.request.response.redirect(
                    mailfolder.absolute_url()+'/view')
            return None

        parent = mailfolder.getMailFolder()
        if parent is not None and hasattr(parent, new_name):
            if self.request is not None:
                psm  = '%s already exists' % new_name
                self.request.response.redirect(
                    mailfolder.absolute_url()+
                    '/view?edit_name=1&msm=%s' % psm)
            return None

        # truncates the name in case it's bigger than 20
        if len(new_name) > max_folder_size:
            new_name = new_name[:max_folder_size]

        try:
            renamed = mailfolder.rename(new_name)
        except ConnectionError:
            renamed = False
            psm = 'cpsma_could_not_perform'

        if renamed:
            fullname = mailfolder.server_name
            folder = getFolder(mailbox, fullname)
        else:
            folder = mailfolder

        if self.request is not None:
            resp = self.request.response
            if renamed:
                resp.redirect(folder.absolute_url()+'/view')
            else:
                resp.redirect(folder.absolute_url()+'/view?msm=%s' % psm)
        else:
            return folder

    def delete(self):
        """ action called to rename the current folder """
        mailfolder = self.context
        title = mailfolder.title
        try:
            deleted = mailfolder.delete()
            psm = 'Folder %s sent to the trash.' % title
        except ConnectionError:
            deleted = None
            psm = 'cpsma_could_not_perform'

        # deleted is the new place for the folder
        if self.request is not None:
            if deleted is not None:
                # let's go to the mailbox INBOX
                mailbox = mailfolder.getMailBox()
                if hasattr(mailbox, 'INBOX'):
                    goto = mailbox['INBOX']
                else:
                    goto = mailbox
                url = goto.absolute_url()
            else:
                url = mailfolder.absolute_url()
            self.request.response.redirect(url+'/view?msm=%s' % psm)

    def _sortMessages(self, elements, sort_with, sort_asc):
        """ sorts a list of messages """
        if sort_with not in ('Attachments', 'Subject', 'From', 'Date',
                             'Size', 'Icon'):
            sort_with = 'Date'

        sort_list = []
        for element in elements:
            if sort_with == 'Attachments':
                if element.hasAttachment():
                    sorter = 1
                else:
                    sorter = 0
            elif sort_with == 'Subject':
                if IMailMessage.providedBy(element):
                    subject = element.getHeader('Subject')
                    if subject != []:
                        translated_title = decodeHeader(subject[0])
                        mail_title = translated_title
                    else:
                        mail_title = '?'
                else:
                    ob_title = self.createShortTitle(element)
                    if ob_title is None or ob_title == '':
                        mail_title = '?'
                    else:
                        mail_title = ob_title
                sorter = mail_title
            elif sort_with == 'From':
                element_from = element.getHeader('From')
                if element_from is None or element_from == []:
                    element_from = u'?'

                sorter = decodeHeader(element_from[0])
            elif sort_with == 'Date':
                element_date = element.getHeader('Date')
                if element_date is None or element_date == []:
                    element_date = '?'
                stDate = decodeHeader(element_date[0])
                sorter = parseDateString(stDate)
            elif sort_with == 'Size':
                if element.size is not None:
                    sorter = int(element.size)
                else:
                    sorter = -1
            elif sort_with == 'Icon':
                sorter = self.getMsgIconName(element)
            else:
                sorter = 0

            sort_list.append((sorter, element))

        sort_list.sort()
        if not sort_asc:
            sort_list.reverse()

        return [element[1] for element in sort_list]

    def getLastMailListSortCache(self):
        """ returns the last parameters used for sorting """
        mailfolder = self.context
        return mailfolder.getLastMailListSortCache()

    def renderMailList(self, page=1, nb_items=20, sort_with='Date',
                       sort_asc=0, keep_last_sort=0):
        """ renders mailfolder content

        uses a batch
        """
        if self._last_error is not None:
            return []

        mailfolder = self.context
        if int(keep_last_sort) == 1:
            founded = self.getLastMailListSortCache()
            if founded is not None:
                # getting back parameters from last sort
                page = founded[0]
                nb_items = founded[1]
                sort_with = founded[2]
                sort_asc = founded[3]

        cache = mailfolder.getMailListFromCache(page, nb_items,
                                                sort_with, sort_asc)
        if cache is not None:
            return cache

        returned = []
        elements = mailfolder.getMailMessages(list_folder=False,
            list_messages=True, recursive=False)

        # removing deleted message if not in Trash
        box = mailfolder.getMailBox()
        if box is not None and mailfolder != box.getTrashFolder():
            new_list = []
            for element in elements:
                if element.deleted != 1:
                    new_list.append(element)
        else:
            new_list = elements

        # now cutting in nb_items
        nb_elements = len(elements)
        nb_pages = int(ceil(float(nb_elements) / float(nb_items)))

        # calculating the slice
        if page >= nb_pages:    # first page starts at 1
            page = nb_pages

        first_element = (page - 1) * nb_items
        last_element =  first_element + nb_items

        if last_element >= nb_elements:
            last_element = nb_elements - 1

        # sorting before slicing
        elements = self._sortMessages(new_list, sort_with, sort_asc)

        # slicing
        elements = elements[first_element:last_element+1]

        i = 0

        for element in elements:
            part = {}
            part['object'] = element
            part['Icon'] = self.getMsgIconName(element)
            part['url'] = element.absolute_url() +'/view'
            part['uid'] = element.uid
            part['folder_id_uid'] = '%s__%s' % (mailfolder.server_name,
                                                element.uid)

            if element.hasAttachment():
                part['Attachments'] = 1
            else:
                part['Attachments'] = 0

            if IMailMessage.providedBy(element):
                subject = element.getHeader('Subject')
                if subject != []:
                    translated_title = decodeHeader(subject[0])
                    mail_title = secureUnicode(translated_title)
                else:
                    mail_title = u'?'
            else:
                ob_title = self.createShortTitle(element)
                if ob_title is None or ob_title == '':
                    mail_title = u'?'
                else:
                    mail_title = secureUnicode(ob_title)

            part['Subject'] = mail_title

            element_from = element.getHeader('From')
            if element_from is None or element_from == []:
                element_from = u'?'
            part['From'] = secureUnicode(decodeHeader(element_from[0]))

            element_date = element.getHeader('Date')
            if element_date is None or element_date == []:
                element_date = '?'
            date = decodeHeader(element_date[0])
            if isToday(date):
                part['Date'] = localizeDateString(date, 1)
            else:
                part['Date'] = localizeDateString(date, 3)

            if element.size is not None:
                part['Size'] = getHumanReadableSize(element.size)
            else:
                part['Size'] = getHumanReadableSize(-1)

            part['new'] = not element.seen
            returned.append(part)
            i += 1

        mailfolder.addMailListToCache((nb_pages, returned), page, nb_items,
                                      sort_with, sort_asc)
        return (nb_pages, returned)

    def getMsgIconName(self, message):
        """ icon representing the mail depends on flags """
        deleted = message.getFlag('deleted')
        if deleted == 1:
            return 'cpsma_mini_mail_delete.png'

        seen = message.getFlag('seen')
        answered = message.getFlag('answered')
        forwarded = message.getFlag('forwarded')

        if seen == 0:
            return 'cpsma_message_new.png'
        if answered == 1 and forwarded == 0:
            return 'cpsma_replied.png'
        if answered == 1 and forwarded == 1:
            return 'cpsma_replied_forward.png'
        if forwarded == 1:
            return 'cpsma_mini_mail_forward.png'

        # todo : create more icons here
        # flagged = message.getFlag('flagged')
        return 'cpsma_message.png'

    def addFolder(self, name):
        """ adds a folder """
        mailfolder = self.context
        max_folder_size = self.getMaxFolderSize()
        if len(name) > max_folder_size:
            name = name[:max_folder_size]

        if not mailfolder.hasKey(name):
            server_name = mailfolder.server_name + '.' + name
            try:
                new_folder = mailfolder._addFolder(name, server_name, True)
            except ConnectionError:
                new_folder = None
                psm = 'cpsma_could_not_perform'
        else:
            new_folder = mailfolder[name]

        if self.request is not None:
            resp = self.request.response
            if new_folder is not None:
                resp.redirect(new_folder.absolute_url()+'/view')
            else:
                resp.redirect(mailfolder.absolute_url()+'/view?msm=%s' % psm)

    def getMessageUidAndFolder(self, id):
        """ get message from id

        Structure : server_name.uid
        """
        mailfolder = self.context
        mailbox = mailfolder.getMailBox()
        path = id.split('.')
        msg_id = path[len(path)-1]
        del path[len(path)-1]
        current = mailbox
        for element in path:
            childfolders = current.getchildFolders()
            found = 0
            for childfolder in childfolders:
                if childfolder.title == element:
                    found = 1
                    break
            if found == 1:
                current = childfolder
            else:
                return None, None

        msg_uid = current.getIdFromUid(msg_id)

        if not current.has_key(msg_uid):
            return current, None
        msg = current[msg_uid]
        return current, msg.uid

    def manageContent(self, action=None, **kw):
        """ manage content """
        if self.request is not None:
            if self.request.form is not None:
                for element in self.request.form.keys():
                    kw[element] = self.request.form[element]

        if action is None:
            for key in kw.keys():
                if key.startswith('action_'):
                    action = key[7:]
                    break

        mailfolder = self.context
        psm = ''

        if action in ('copy', 'cut', 'delete', 'clear'):
            mailbox = mailfolder.getMailBox()
            if action == 'clear':
                mailbox.clearClipboard()
            msg_list = []
            for key in kw.keys():
                if key.startswith('msg_'):
                    id = mailfolder.server_name +'.' + key.replace('msg_', '')
                    msg_list.append(id)
            if msg_list != []:
                if action == 'copy':
                    mailbox.fillClipboard('copy', msg_list)
                if action == 'cut':
                    mailbox.fillClipboard('cut', msg_list)
                if action == 'delete':
                    interrupted = False
                    for msg in msg_list:
                        folder, uid = self.getMessageUidAndFolder(msg)
                        res = folder.deleteMessage(uid)
                        if not res:
                            psm = 'cpsma_could_not_perform'
                            interrupted = True
                            break
                    if not interrupted:
                        if len(msg_list) > 1:
                            psm = 'cpsma_msgs_sent_to_trash'
                        else:
                            psm = 'cpsma_msg_sent_to_trash'
        if action == 'paste':
            mailbox = mailfolder.getMailBox()
            past_action, ids = mailbox.getClipboard()
            if ids is not None:
                try:
                    if past_action == 'cut':
                        # it's a cut'n'paste
                        for id in ids:
                            folder, uid = self.getMessageUidAndFolder(id)
                            res = folder.moveMessage(uid, mailfolder)
                            if not res:
                                psm = 'cpsma_could_not_perform'
                                break
                    else:
                        # it's a copy
                        for id in ids:
                            folder, uid = self.getMessageUidAndFolder(id)
                            res = folder.copyMessage(uid, mailfolder)
                            if not res:
                                psm = 'cpsma_could_not_perform'
                                break
                finally:
                    mailbox.clearClipboard()

        if self.request is not None:
            # let's go to the mailbox
            url = mailfolder.absolute_url()

            if psm == '':
                self.request.response.redirect(url+'/view')
            else:
                self.request.response.redirect(url+
                    '/view?msm=%s' % psm)

    def clipBoardEmpty(self):
        """ tells if the clipboard is empty or not

        If not empty, leaves the cut-copy-paste toolbar
        on screen
        """
        mailfolder = self.context
        mailbox = mailfolder.getMailBox()
        return mailbox.clipBoardEmpty()

    def clipBoardCount(self):
        """ returns clipboard item count """
        mailfolder = self.context
        mailbox = mailfolder.getMailBox()
        action, clipboard = mailbox.getClipboard()
        if clipboard is None:
            return 0
        return len(clipboard)

    def getMessageListCols(self):
        """ returns the list of cols """
        mailfolder = self.context
        mailbox = mailfolder.getMailBox()
        list_cols = mailbox.getConnectionParams()['message_list_cols']
        list_cols = [item.strip() for item in list_cols.split(',')]
        return list_cols

    def runFilters(self):
        """ runs filters """
        mailfolder = self.context
        mailfolder.runFilters()

        if self.request is not None:
            # let's go to the mailbox
            url = mailfolder.absolute_url()
            self.request.response.redirect(url+'/view')
