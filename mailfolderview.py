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
from zLOG import LOG, INFO, DEBUG
from basemailview import BaseMailMessageView
from utils import decodeHeader, localizeDateString, isToday
from interfaces import IMailMessage

class MailFolderView(BaseMailMessageView):

    def __init__(self, context, request):
        BaseMailMessageView.__init__(self, context, request)

    def rename(self, new_name):
        """ action called to rename the
            current folder
        """
        mailfolder = self.context

        if mailfolder.title == new_name:
            if self.request is not None:
                self.request.response.redirect(
                    mailfolder.absolute_url()+'/view')
            return

        parent = mailfolder.getMailFolder()
        if parent is not None and hasattr(parent, new_name):
            if self.request is not None:
                psm  = '%s already exists' % new_name
                self.request.response.redirect(
                    mailfolder.absolute_url()+'/view?edit_name=1&portal_status_message=%s' % psm)
            return

        renamed = mailfolder.rename(new_name)

        if self.request is not None and renamed is not None:
            self.request.response.redirect(renamed.absolute_url()+'/view')

    def delete(self):
        """ action called to rename the current folder
        """
        mailfolder = self.context
        deleted = mailfolder.delete()
        if self.request is not None and deleted:
            # let's go to the mailbox
            url = mailfolder.getMailBox().absolute_url()
            self.request.response.redirect(url+'/view')

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
            if element_from is None:
                element_from = '?'
            part['From'] = decodeHeader(element_from)
            element_date = element.getHeader('Date')
            if element_date is None:
                element_date = '?'
            date = decodeHeader(element_date)
            if isToday(date):
                part['Date'] = localizeDateString(date, 2)
            else:
                part['Date'] = localizeDateString(date, 3)
            returned.append(part)
        return returned

    def getMsgIconName(self, message):
        """ icon representing the mail depends on flags
        """
        read = message.getFlag('read')
        if read == 0:
            return 'cpsma_message_new.png'
        deleted = message.getFlag('deleted')
        if deleted == 1:
            return 'cpsma_mini_mail_delete.png'
        # todo : create more icons here
        answered = message.getFlag('answered')
        flagged = message.getFlag('flagged')
        forwarded = message.getFlag('forwarded')
        return 'cpsma_message.png'

    def addFolder(self, name):
        """ adds a folder
            XXX todo:doit on server's side
        """
        mailfolder = self.context
        if not hasattr(mailfolder, name):
            server_name = mailfolder.server_name + '.' + name
            new_folder = mailfolder._addFolder(name, server_name)
        else:
            new_folder = getattr(mailfolder, name)
        if self.request is not None and new_folder is not None:
            self.request.response.redirect(new_folder.absolute_url()+'/view')
