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
from utils import getToolByName, getCurrentDateStr, _isinstance,\
     decodeHeader, verifyBody, cleanUploadedFileName
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
from email import base64MIME

class MailMessageEdit(BrowserView):

    def initMessage(self):
        """ will init message editor
        """
        mailbox = self.context
        # this creates a mailmessage instance
        # XXX todo manage a list of editing message in case of multiediting
        #mailbox.getCurrentEditorMessage()

    def sendMessage(self, msg_from, msg_subject, msg_body, came_from=None):
        """ calls MailTool
        """
        """self.context.GetHTML
        raise str(msg_body)
        """
        # call mail box to send a message and to copy it to "send" section
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        msg.setHeader('Subject', msg_subject)
        Tos = msg.getHeader('To')
        if Tos == []:
            if self.request is not None:
                # todo : need to be externalized in i18n
                psm = 'Recipient is required'
                self.request.response.redirect('editMessage.html?portal_status_message=%s'\
                    % (psm))
            return

        msg.setHeader('From', msg_from)
        msg_body = verifyBody(msg_body)

        # this needs to be done in an api inside mailpart
        if not msg.isMultipart():
            msg.setPart(0, msg_body)
        else:
            # the mail editor message structure does not move
            sub = msg.getPart(0)
            sub._payload = msg_body
            msg.setPart(0, sub)

        # using the message instance that might have attached files already
        result, error = self.context.sendEditorsMessage()


        if self.request is not None:
            if result:
                if came_from is not None and came_from !='':
                    goto = came_from
                else:
                    if hasattr(mailbox, 'INBOX'):
                        goto = mailbox.INBOX.absolute_url()
                    else:
                        goto = mailbox.absolute_url()

                # todo : need to be externalized
                psm = 'Message sent.'
                self.request.response.redirect('%s/view?portal_status_message=%s'\
                    % (goto, psm))
            else:
                goto = mailbox.absolute_url()+'/editMessage.html'
                psm = error
                self.request.response.redirect('%s?portal_status_message=%s'\
                    % (goto, psm))
        else:
            return result, error


    def getIdentitites(self):
        """ gives to the editor the list of current m�ailbox idendities
        """
        mailbox = self.context
        identities = mailbox.getIdentitites()
        return identities

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

        # beware of IE under win : need to get rid of filename path
        # and this is specific on client side
        # hack : try to see if it's a windows path
        # by searching ':/'
        file.filename = cleanUploadedFileName(file.filename)

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
        try:
            res = msg.getPart(0)
            if res is None:
                return ''
        except IndexError:
            res = ''

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
        if res is None or res == []:
            return ''
        #msg_viewer = MailMessageView(msg, self.request)
        return decodeHeader(res[0])

    def getDestList(self):
        """ returns dest list
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        res = []
        for part in ('To', 'Cc', 'BCc'):
            content = msg.getHeader(part)
            if content is not None and content <> []:
                for element in content:
                    res.append({'value' : decodeHeader(element),
                        'type' : part})
        return res

    def saveMessageForm(self):
        """ saves the form into the message
        """
        if self.request is None:
            return
        form = self.request.form
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()

        if form.has_key('msg_body'):
            msg_body = form['msg_body']
            msg.setPart(0, msg_body)

        if form.has_key('msg_subject'):
            msg_subject = form['msg_subject']
            msg.setHeader('Subject', msg_subject)

        return 'ok'

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

        msg.removeHeader(type, [value])

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

        # ; and , for mail separators
        content = content.replace(';', ',')
        mails = content.split(',')

        for mail in mails:
            mail = mail.strip()
            list_ = msg.getHeader(type)
            if mail not in list_:
                msg.addHeader(type, mail)

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
            if kw.has_key('came_from'):
                came_from = kw['came_from']
            else:
                came_from = None
            self.sendMessage(kw['msg_from'], kw['msg_subject'],
                             kw['msg_body'], came_from)

    def saveMessage(self):
        """ saves the message in Drafts
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        identity = mailbox.getIdentitites()[0]
        msg_from = '%s <%s>' %(identity['fullname'], identity['email'])
        msg_subject = '?'
        msg.setHeader('From', msg_from)
        msg.setHeader('Subject', msg_subject)
        mailbox.saveEditorMessage()

        if self.request is not None:
            psm = 'Message has been saved in Drafts'
            self.request.response.redirect('editMessage.html\
                                            ?portal_status_message=%s' % psm)

    def initializeEditor(self):
        """ cleans the editor
        """
        mailbox = self.context
        mailbox.clearEditorMessage()

        if self.request is not None:
            self.request.response.redirect('editMessage.html')
