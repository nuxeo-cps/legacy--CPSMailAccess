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

from zLOG import LOG, DEBUG, INFO
from Globals import InitializeClass
import sys
from smtplib import SMTP
from utils import getToolByName, getCurrentDateStr, _isinstance, decodeHeader
import thread
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from Products.Five import BrowserView
from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from zope.publisher.browser import FileUpload
from utils import uniqueId, makeId, getFolder
from interfaces import IMailBox, IMailMessage, IMailFolder
from mailmessage import MailMessage
from mailfolder import MailFolder, manage_addMailFolder
from mailfolderview import MailFolderView
from baseconnection import ConnectionError, BAD_LOGIN, NO_CONNECTOR
from mailcache import MailCache
from basemailview import BaseMailMessageView
from mailmessageview import MailMessageView

class MailMessageEdit(BrowserView):

    def initMessage(self):
        """ will init message editor
        """
        mailbox = self.context
        # this creates a mailmessage instance
        # XXX todo manage a list of editing message in case of multiediting
        mailbox.getCurrentEditorMessage()

    def sendMessage(self, msg_from, msg_to, msg_subject, msg_body,
            msg_attachments=[], came_from=None):
        """ calls MailTool
        """
        # call mail box to send a message and to copy it to "send" section
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()

        msg.setHeader('From', msg_from)
        msg.setHeader('To', msg_to)
        msg.setHeader('Subject', msg_subject)

        # XX todo load body according to attached parts
        msg.setPart(0, msg_body)

        # using the message instance that might have attached files already
        result = self.context.sendEditorsMessage()

        if self.request is not None and came_from is not None:
            if result:
                self.request.response.redirect(came_from)
            else:
                #XXXX need to redirect to an error screen here later
                psm ='Message Sent'
                self.request.response.redirect('view?portal_status_message=%s' % psm)

    def getIdentitites(self):
        """ gives to the editor the list of current m�ailbox idendities
        """
        # XXXX todo
        identity = {'email' : 'tarek@ziade.org', 'fullname' : 'Tarek Ziad�'}

        return [identity]

    def is_editor(self):
        """ tells if we are in editor view (hack)
        """
        if self.request is not None:
            url_elements = self.request['URL'].split('/')
            len_url = len(url_elements)
            return url_elements[len_url-1]=='editMessage.html'
        else:
            return False

    def attached_files(self):
        """ gets attached file list
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        msg_viewer = MailMessageView(msg, self.request)
        return msg_viewer.attached_files()

    def attachFile(self, file):
        """ attach a file to the current message
        """
        if file == '':
            return
        # file is the file name
        # need to load binary here
        mailbox = self.context
        #max_size = mailbox.max_file_size
        max_size = 0
        msg = mailbox.getCurrentEditorMessage()
        #if not _isinstance(file, FileUpload) or not type(file) is FileUpload:
        #    raise TypeError('%s' % str(type(file)))
        if file.read(1) == '':
            return
        elif max_size and len(file.read(max_size)) == max_size:
            raise FileError('file is too big')

        msg.attachFile(file)
        if self.request is not None:
            self.request.response.redirect('editMessage.html')

    def detachFile(self, filename):
        """ detach a file
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()

        msg.detachFile(filename)

        if self.request is not None:
            self.request.response.redirect('editMessage.html')

    def getBodyValue(self):
        """ returns body value
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        # XXX should be inside message and called thru an api
        res = msg.getPart(0)
        if type(res) is str:
            return res
        else:
            return res.get_payload()

    def getSubject(self):
        """ returns subject value
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        # XXX should be inside message and called thru an api
        res = msg.getHeader('Subject')
        if res is None:
            return ''
        #msg_viewer = MailMessageView(msg, self.request)
        return decodeHeader(res)

    def getDestList(self):
        """ returns dest list
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        res = []

        for part in ('To', 'Cc', 'BCc'):

            content = msg.getHeader(part)
            if content is not None:
                content = content.split(' ')
                for cpart in content:
                    res.append({'value' : decodeHeader(cpart),
                        'type' : part})
        return res

    def saveMessageForm(self, msg_from=None, msg_to=None, msg_subject=None,
            msg_body=None):
        """ saves the form into the message
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        if msg_from is not None:
            msg.setHeader('From', msg_from)
        if msg_to is not None:
            if type(msg_to) is str:
                msg.setHeader('To', msg_to)
            else:
                msg.setHeader('To', ' '.join(msg_to))
        if msg_subject is not None:
            msg.setHeader('Subject', msg_subject)
        if msg_body is not None:
            msg.setPart(0, msg_body)

    def removeRecipient(self, value, type):
        """ removes a recipient
        """
        content = value.strip()
        if content == '':
            return
        if not type in('To', 'Cc', 'BCc'):
            type = 'To'
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        List = msg.getHeader(type)
        if List is None:
            List = []
        else:
            List = List.split(' ')

        if content in List:
            List.remove(content)
            result = ' '.join(List)
            msg.setHeader(type, result)

        if self.request is not None:
            self.request.response.redirect('editMessage.html')

    def addRecipient(self, content, type):
        """ add a recipient
        """
        content = content.strip()
        if content == '':
            return
        if not type in('To', 'Cc', 'BCc'):
            type = 'To'
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        List = msg.getHeader(type)
        if List is None:
            List = []
        else:
            List = List.split(' ')
        if content not in List:
            List.append(content)
            result = ' '.join(List)
            msg.setHeader(type, result)

        if self.request is not None:
            self.request.response.redirect('editMessage.html')


    def editAction(self, action, **kw):
        """ dispatch a form action to the right method
        """
        if self.request is not None:
            if self.request.form is not None:
                for element in self.request.form.keys():
                    kw[element] = self.request.form[element]

        if action == 'add_recipient':
            self.addRecipient(kw['msg_to'], kw['sent_type'])
        if action == 'remove_recipient':
            self.removeRecipient(kw['msg_to'], kw['sent_type'])
        elif action == 'send':
            if not kw.has_key('msg_attachments'):
                kw['msg_attachments'] = []

            if not kw.has_key('came_from'):
                kw['came_from'] = []

            self.sendMessage(kw['msg_from'], kw['msg_to'], kw['msg_subject'],
                kw['msg_attachments'], kw['came_from'])
