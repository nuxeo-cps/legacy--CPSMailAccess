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
from zLOG import LOG, DEBUG, INFO

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from interfaces import IMailMessage, IMailFolder, IMailBox, IMailPart
from utils import decodeHeader, parseDateString, localizeDateString, \
    truncateString, mimetype_to_icon_name, getFolder
from Globals import InitializeClass
from Products.Five import BrowserView
from mailrenderer import MailRenderer
from basemailview import BaseMailMessageView
from mailpart import MailPart
from mailfolderview import MailFolderView
from email import message_from_string

class MailMessageView(BaseMailMessageView):

    _RenderEngine = MailRenderer()
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def renderDate(self):
        """ renders the mail date
        """
        if self.context is not None:
            date = self.context.getHeader('Date')
            if date is None:
                date = '?'
            else:
                date = decodeHeader(date)
        else:
            date = '?'
        date = localizeDateString(date)
        return date

    def renderSmallDate(self):
        """ renders the mail date
        """
        if self.context is not None:
            date = self.context.getHeader('Date')
            if date is None:
                date = '?'
            else:
                date = decodeHeader(date)
        else:
            date = '?'
        date = localizeDateString(date, 3)
        return date

    def renderSubject(self):
        """ renders the mail subject
        """
        if self.context is not None:
            subject = self.context.getHeader('Subject')
            if subject is None:
                subject = '?'
            else:
                subject = decodeHeader(subject)
        else:
            subject = '?'
        return subject

    def renderFromList(self):
        """ renders the mail From
        """
        if self.context is not None:
            froms = self.context.getHeader('From')
            if froms is None:
                froms = '?'
            else:
                froms = decodeHeader(froms)
        else:
            froms = '?'
        return froms

    def renderToList(self):
        """ renders the mail list
        """
        if self.context is not None:
            tos = self.context.getHeader('To')
            if tos is None:
                tos = '?'
            else:
                tos = decodeHeader(tos)
        else:
            tos = '?'
        return tos


    def _bodyRender(self, mail, part_index):
        return self._RenderEngine.renderBody(mail, part_index)

    def renderBody(self):
        """ renders the mail body
        """
        if self.context is not None:
            mail = self.context
            #### the user reads the messge, let's
            # sets the read message to 1
            mail.setFlag('read', 1)

            # do we have everything to show ?
            # here loadParts will automatically
            # create caches, fetchs things
            part_count = mail.getPartCount()
            if part_count > 0:
                for i in range(part_count):
                    mail.loadPart(i)

                body = self._bodyRender(mail, 0)
            else:
                body = ''
        else:
            body = ''
        return body

    def renderMailList(self):
        """ renders mail message list given by the folder
            XXX duplicated from folder view,
            need to get folder's view
            if this list does not differ from the folder's one
        """
        mailfolder = self.context.aq_inner.aq_parent
        mailfolder_view = MailFolderView(mailfolder, self.request)
        return mailfolder_view.renderMailList()

    def reply(self):
        """ replying to a message
            is writing a message with a given "to" "from"
            and with a given body
        """
        # getting mailbox
        # Zope 2 code, need to put in in utils
        mailbox = self.context.getMailBox()

        # let's compute the pre-filled body
        # XXX todo : add "MrJohn Doe wrote....
        # TODO : get the body and parseit here
        body_value = '>>> wrote'

        if self.request is not None:
            self.request.form['came_from'] = self.context.absolute_url()
            self.request.response.redirect('%s/editMessage.html?body_value=%s'\
                % (mailbox.absolute_url(), body_value))

    def reply_all(self):
        """ replying to a message
            is writing a message with a given "to" "from"
            and with a given body
        """
        # getting mailbox
        # Zope 2 code, need to put in in utils
        mailbox = self.context.getMailBox()

        # let's compute the pre-filled body
        # XXX todo : add "MrJohn Doe wrote....
        # TODO : get the body and parseit here
        body_value = '>>> wrote'

        if self.request is not None:
            self.request.form['came_from'] = self.context.absolute_url()
            self.request.response.redirect('%s/editMessage.html' % mailbox.absolute_url())

    def forward(self):
        """ replying to a message is writing a message with a given "to" "from"
            and with a given body
        """
        # getting mailbox
        # Zope 2 code, need to put in in utils
        mailbox = self.context.getMailBox()
        # TODO create an attached file
        if self.request is not None:
            self.request.form['came_from'] = self.context.absolute_url()
            self.request.response.redirect('%s/editMessage.html' % mailbox.absolute_url())

    def delete(self):
        """ "deletes" the message (copy it to the thrash indeed)
        """
        mailbox = self.context.getMailBox()
        msg = self.context
        msg_container = msg.getMailFolder()
        trash_folder = mailbox.getTrashFolder()
        # deletes it locally *and* from server
        msg_container.moveMessage(msg.uid, trash_folder)
        # need to do the same on server
        msg.setFlag('deleted', 1)

        if self.request is not None:
            folder = msg_container.absolute_url()
            self.request.response.redirect('%s/view' % folder)

    def attached_files(self):
        # todo :scans attached files
        message = self.context
        if not message.isMultipart():
            return []
        list_files = []

        #LOG('att', INFO, str(message.getRawMessage()))

        for part in range(message.getPartCount()):
            # XX todo : avoid re-generate part on each visit : use caching
            part_ob = MailPart('part_'+str(part), message, message.getPart(part))
            infos = part_ob.getFileInfos()
            if infos is not None:
                # let's append icon, url, and title
                infos['url'] = str(part)+'/'+str(infos['filename'])
                infos['icon'] =  mimetype_to_icon_name(infos['mimetype'])
                title = infos['filename']
                if len(title) > 10:
                    title = title[:7] +'...'
                infos['title'] = title
                infos['delete_url'] = 'delete_attachement?filename=' + infos['filename']
                list_files.append(infos)
        if list_files == []:
            return []
        i = 0
        clist_files = []
        while i < len(list_files):
            if i+1 < len(list_files):
                clist_files.append([list_files[i], list_files[i+1]])
            else:
                clist_files.append([list_files[i]])
            i += 2
        return clist_files
