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


from utils import uniqueId, makeId, getFolder, isValidEmail
from interfaces import IMailBox, IMailMessage, IMailFolder
from mailmessage import MailMessage
from mailfolder import MailFolder, manage_addMailFolder
from mailfolderview import MailFolderView
from baseconnection import ConnectionError, BAD_LOGIN, NO_CONNECTOR

from basemailview import BaseMailMessageView
from mailmessageview import MailMessageView
from email import base64MIME

class MailMessageEdit(BrowserView):

    def getFlag(self, name):
        """ returns a flag """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        value = msg.getCachedValue(name)
        if value is None:
            return 0
        else:
            return value

    def initMessage(self):
        """ will init message editor """
        mailbox = self.context
        # this creates a mailmessage instance
        # XXX todo manage a list of editing message in case of multiediting
        #mailbox.getCurrentEditorMessage()

    def writeTo(self, msg_to):
        """ initialize maileditor """
        mailbox = self.context
        mailbox.clearEditorMessage()
        msg = mailbox.getCurrentEditorMessage()
        msg.setHeader('To', msg_to)
        if self.request is not None:
            self.request.response.redirect('editMessage.html')

    def _verifyRecipients(self, msg):
        """ verify all recipients """
        verify_fields = ('To', 'Cc', 'BCc')
        for field in verify_fields:
            values = msg.getHeader(field)
            for value in values:
                if not isValidEmail(value):
                    return '%s is not a valid email' % value
        return None

    def sendMessage(self, msg_from, msg_subject, msg_body, came_from=None):
        """ calls MailTool """
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

        error = self._verifyRecipients(msg)
        if error is not None:
            if self.request is not None:
                # todo : need to be externalized in i18n
                psm = error
                self.request.response.redirect('editMessage.html?portal_status_message=%s'\
                    % (psm))
            return

        msg.setHeader('From', msg_from)
        msg_body = verifyBody(msg_body)
        msg.setDirectBody(msg_body)

        if msg_subject.strip() == '' and msg_body.strip() == '':
            if self.request is not None:
                # todo : need to be externalized in i18n
                psm = 'both subject and body are empty'
                self.request.response.redirect('editMessage.html?portal_status_message=%s'\
                    % (psm))
            return

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
        """ gives to the editor the list of current mùailbox idendities """
        mailbox = self.context
        identities = mailbox.getIdentitites()
        return identities

    def _identyToMsgHeader(self):
        """ takes a directory entry to fit it in From header """
        identities = self.getIdentitites()
        if len(identities) > 0:
            identity = identities[0]        # think about multi-identity later
            return '%s <%s>' %(identity['fullname'], identity['email'])
        else:
            return '?'

    def is_editor(self):
        """ tells if we are in editor view (hack) """
        if self.request is not None:
            url_elements = self.request['URL'].split('/')
            len_url = len(url_elements)
            return url_elements[len_url-1]=='editMessage.html'
        else:
            return False

    def attached_files(self):
        """ gets attached file list
        """
        if self.request is not None:
            # XXX this is a ugly hack, need to do better thru zcml
            if not self.request['URL'].endswith('editMessage.html'):
                return []
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        msg_viewer = MailMessageView(msg, self.request)
        return msg_viewer.attached_files()

    def attachFile(self, file):
        """ attach a file to the current message
        """
        if file == '':
            return
        for line in self.attached_files():
            for cfile in line:
                if cfile['filename'].lower() == file.filename.lower():
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
        msg.setCachedValue('attacher_on', 0)
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
        """ returns body value """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        return msg.getDirectBody()

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

    def getDestList(self, type_='To'):
        """ returns dest list
        """
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()
        res = []
        content = msg.getHeader(type_)
        if content is not None and content <> []:
            for element in content:
                res.append(decodeHeader(element))
        return res

    def saveMessageForm(self):
        """ saves the form into the message """
        if self.request is None:
            return
        form = self.request.form
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()

        if form.has_key('msg_body'):
            msg_body = form['msg_body']
            msg.setDirectBody(msg_body)

        if form.has_key('msg_subject'):
            msg_subject = form['msg_subject']
            msg.setHeader('Subject', msg_subject)

        textareas = (('msg_to', 'To'), ('msg_cc', 'Cc'), ('msg_bcc', 'BCc'))

        for area, id in textareas:
            if form.has_key(area):
                msg_body = form[area]
                lines = msg_body.split('\r\n')
                msg.removeHeader(id)            # otherwise previou ones stays there
                self.addRecipient(msg_body, id)

        if form.has_key('cc_on'):
            msg.setCachedValue('cc_on', int(form['cc_on']))

        if form.has_key('bcc_on'):
            msg.setCachedValue('bcc_on', int(form['bcc_on']))

        if form.has_key('attacher_on'):
            msg.setCachedValue('attacher_on', int(form['attacher_on']))

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
        if not type in ('To', 'Cc', 'BCc'):
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
        msg_from = self._identyToMsgHeader()
        msg.setHeader('From', msg_from)
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
