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
from zLOG import LOG, INFO, DEBUG
from basemailview import BaseMailMessageView
from utils import decodeHeader, localizeDateString, parseDateString, \
    isToday, getFolder
from interfaces import IMailMessage

class MailFolderView(BaseMailMessageView):

    def __init__(self, context, request):
        BaseMailMessageView.__init__(self, context, request)

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
                    '/view?edit_name=1&portal_status_message=%s' % psm)
            return None

        # truncates the name in case it's bigger than 20
        if len(new_name) > max_folder_size:
            new_name = new_name[:max_folder_size]

        renamed = mailfolder.rename(new_name)

        fullname = mailfolder.server_name

        folder = getFolder(mailbox, fullname)

        if self.request is not None and renamed is not None:
            self.request.response.redirect(folder.absolute_url()+'/view')
        else:
            return folder

    def delete(self):
        """ action called to rename the current folder
        """
        mailfolder = self.context
        title = mailfolder.title
        deleted = mailfolder.delete()
        # deleted is the new place for the folder
        if self.request is not None and deleted is not None:
            psm = 'Folder %s sent to the trash.' % title
            # let's go to the mailbox INBOX
            mailbox = mailfolder.getMailBox()
            if hasattr(mailbox, 'INBOX'):
                goto = mailbox['INBOX']
            else:
                goto = mailbox
            url = goto.absolute_url()
            self.request.response.redirect(url+'/view?portal_status_message=\
                                           %s' % psm)

    def renderMailList(self):
        """ renders mailfolder content

        XXX need to externalize html here
        """
        mailfolder = self.context
        returned = []
        elements = mailfolder.getMailMessages(list_folder=False,
            list_messages=True, recursive=False)
        for element in elements:
            part = {}
            part['object'] = element
            part['icon'] = self.getMsgIconName(element)
            part['url'] = element.absolute_url() +'/view'
            part['uid'] = element.uid

            if element.hasAttachment():
                part['attachments'] = 1
            else:
                part['attachments'] = 0
            ob_title = self.createShortTitle(element)
            if ob_title is None or ob_title == '':
                mail_title = '?'
            else:
                if IMailMessage.providedBy(element):
                    translated_title = decodeHeader(ob_title)
                    mail_title = translated_title
                else:
                    mail_title = ob_title
            part['title'] = mail_title
            element_from = element.getHeader('From')
            if element_from is None or element_from == []:
                element_from = '?'
            part['From'] = decodeHeader(element_from[0])
            element_date = element.getHeader('Date')
            if element_date is None or element_date == []:
                element_date = '?'
            date = decodeHeader(element_date[0])
            if isToday(date):
                part['Date'] = localizeDateString(date, 1)
            else:
                part['Date'] = localizeDateString(date, 3)
            part['FullDate'] = parseDateString(date)
            returned.append((part['FullDate'], part))

        # now sorting upon date
        returned.sort()
        returned.reverse()        # most recent on top
        return [element[1] for element in returned]

    def getMsgIconName(self, message):
        """ icon representing the mail depends on flags
        """
        deleted = message.getFlag('deleted')
        if deleted == 1:
            return 'cpsma_mini_mail_delete.png'

        read = message.getFlag('read')
        answered = message.getFlag('answered')
        forwarded = message.getFlag('forwarded')

        if read == 0:
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
        """ adds a folder
            XXX todo:do it on server's side
        """
        # ugly transtypnig
        mailfolder = self.context
        mailbox = mailfolder.getMailBox()

        max_folder_size = self.getMaxFolderSize()
        if len(name) > max_folder_size:
            name = name[:max_folder_size]


        if not mailfolder.hasKey(name):
            server_name = mailfolder.server_name + '.' + name
            new_folder = mailfolder._addFolder(name, server_name, True)
        else:
            new_folder = mailfolder[name]
        if self.request is not None and new_folder is not None:
            self.request.response.redirect(new_folder.absolute_url()+'/view')

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

        if not hasattr(current, msg_uid):
            return current, None
        msg = getattr(current, msg_uid)
        return current, msg.uid

    def manageContent(self, action, **kw):
        """ manage content """
        mailfolder = self.context
        changed = 0
        psm = ''

        if self.request is not None:
            if self.request.form is not None:
                for element in self.request.form.keys():
                    kw[element] = self.request.form[element]

        if action in('copy', 'cut', 'delete', 'clear'):
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
                    for msg in msg_list:
                        folder, uid = self.getMessageUidAndFolder(msg)
                        mailfolder.deleteMessage(uid)
                        changed = 1
                    if len(msg_list) > 1:
                        psm = 'Messages sent to Trash.'
                    else:
                        psm = 'Message sent to Trash.'
        if action == 'paste':
            mailbox = mailfolder.getMailBox()
            past_action, ids = mailbox.getClipboard()
            try:
                if past_action == 'cut':
                    # it's a cut'n'paste
                    for id in ids:
                        folder, uid = self.getMessageUidAndFolder(id)
                        folder.moveMessage(uid, mailfolder)
                else:
                    # it's a copy
                    for id in ids:
                        folder, uid = self.getMessageUidAndFolder(id)
                        folder.copyMessage(uid, mailfolder)
                changed = 1
            finally:
                mailbox.clearClipboard()

        if changed == 1:
            mailbox.validateChanges()

        if self.request is not None:
            # let's go to the mailbox
            url = mailfolder.absolute_url()

            if psm == '':
                self.request.response.redirect(url+'/view')
            else:
                self.request.response.redirect(url+
                    '/view?portal_status_message=%s' % psm)

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
