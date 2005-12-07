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
from AccessControl import Unauthorized
from Products.Five import BrowserView

from utils import decodeHeader, verifyBody, isValidEmail, \
                  cleanUploadedFileName, Utf8ToIso
from baseconnection import ConnectionError
from mailmessageview import MailMessageView

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

    def getRedirect(self):
        """ computes the best pick for redirection after a mail is sent """
        mailbox = self.context
        if hasattr(mailbox, 'INBOX'):
            # XXX Z2 dependant
            return mailbox.INBOX.absolute_url()
        else:
            # XXX Z2 dependant
            return mailbox.absolute_url()

    def initMessage(self):
        """ will init message editor """
        mailbox = self.context
        # this creates a mailmessage instance
        # XXX todo manage a list of editing message in case of multiediting
        mailbox.getCurrentEditorMessage()

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
                    return 'cpsm_not_valid_mail'
        return None

    def sendMessage(self, msg_from, msg_subject=None, msg_body=None,
                    came_from=None, **kw):
        """ calls MailTool """
        EMPTY = '__#EMPTY#__'

        # complete kw with form
        if self.request is not None:
            for key, value in self.request.form.items():
                kw[key] = Utf8ToIso(value)

        for key in kw:
            if kw[key] == EMPTY:
                kw[key] = ''

        msg_from = self._identyToMsgHeader()

        if msg_subject == EMPTY:
            msg_subject = ''

        if msg_body == EMPTY:
            msg_body = ''

        msg_subject = Utf8ToIso(msg_subject)
        msg_body = Utf8ToIso(msg_body)

        no_redirect =  'responsetype' in kw

        # call mail box to send a message and to copy it to "send" section
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()

        # getting values from request
        if msg_subject is not None:
            msg.setHeader('Subject', msg_subject)

        if msg_body is not None:
            msg_body = verifyBody(msg_body)
            msg.setDirectBody(msg_body)

        if msg_subject is not None:
            if msg_subject.strip() == '' and msg_body.strip() == '':
                # todo :XXX  need to be externalized in i18n
                psm = 'cpsm_empty_subjet_body'
                if self.request is not None and not no_redirect:
                    self.request.response.redirect('editMessage.html?msm=%s'\
                        % (psm))
                return False, psm

        textareas = (('msg_to', 'To'), ('msg_cc', 'Cc'), ('msg_bcc', 'BCc'))

        for area, id in textareas:
            if kw.has_key(area):
                cvalue = kw[area]
                if cvalue.strip() == '':
                    if no_redirect:
                        msg.removeHeader(id)
                    else:
                        continue
                lines = cvalue.split('\n')
                msg.removeHeader(id)            # otherwise previous ones stays there
                for line in lines:
                    if line.strip() != '':
                        self.addRecipient(line, id, no_redirect=True)

        Tos = msg.getHeader('To')
        if Tos == []:
            psm = 'Recipient is required'
            if self.request is not None and not no_redirect:
                # todo : need to be externalized in i18n
                self.request.response.redirect('editMessage.html?msm=%s'\
                    % (psm))
            return False, psm

        error = self._verifyRecipients(msg)

        if error is not None:
            psm = error
            if self.request is not None and not no_redirect:
                # todo : need to be externalized in i18n
                self.request.response.redirect('editMessage.html?msm=%s'\
                    % (psm))
            return False, psm


        msg.setHeader('From', msg_from)

        # using the message instance that might have attached files already
        try:
            result, error = self.context.sendEditorsMessage()
        except ConnectionError, e:
            result = False
            error = str(e)
        except Unauthorized, e:
            result = False
            error = str(e)

        if self.request is not None:
            if result:
                # need to set the answered or forwarded flag
                origin = msg.origin_message
                if origin is not None:
                    folder = origin.getMailFolder()
                    if msg.answerType == 'reply':
                        origin.setFlag('answered', 1)
                        folder.changeMessageFlags(origin, 'answered', 1)
                    else:
                        origin.setFlag('forwarded', 1)
                        folder.changeMessageFlags(origin, 'forwarded', 1)

                # todo : need to be externalized
                psm = 'cpsma_message_sent'

                # clear the editor
                self.initializeEditor(False, no_redirect)
                if not no_redirect:
                    if came_from is not None and came_from !='':
                        goto = came_from
                    else:
                        if hasattr(mailbox, 'INBOX'):
                            goto = mailbox.INBOX.absolute_url()
                        else:
                            goto = mailbox.absolute_url()
                    self.request.response.redirect('%s/view?msm=%s'\
                                                    % (goto, psm))
                else:
                    return True, psm
            else:
                goto = mailbox.absolute_url()+'/editMessage.html'
                psm = error
                if not no_redirect:
                    self.request.response.redirect('%s?msm=%s'\
                                                    % (goto, psm))
                else:
                    return True, psm

        return result, error

    def getIdentitites(self):
        """ gives to the editor the list of current mailbox idendities """
        msg = self.context
        mailbox = msg.getMailBox()
        identities = mailbox.getIdentitites()
        return identities

    def _identyToMsgHeader(self):
        """ takes a directory entry to fit it in From header """
        def cleanEntry(entry):
            for element in (' ', '<', '>', ' '):
                entry = entry.strip(element)
            return entry

        identities = self.getIdentitites()
        if len(identities) > 0:
            identity = identities[0]        # think about multi-identity later
            if identity['email'].strip() == '':
                email = '?'
            else:
                email = cleanEntry(identity['email'])

            if identity['fullname'] != '':
                fullname = cleanEntry(identity['fullname'])
                return '%s <%s>' %(fullname, email)
            else:
                return email
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
        """ attach a file to the current message """
        if file == '':
            return False
        for line in self.attached_files():
            for cfile in line:
                if cfile['filename'].lower() == file.filename.lower():
                    return False

        # file is the file name
        # need to load binary here
        mailbox = self.context
        #max_size = mailbox.max_file_size
        max_size = 0
        msg = mailbox.getCurrentEditorMessage()
        #if not _isinstance(file, FileUpload) or not type(file) is FileUpload:
        #    raise TypeError('%s' % str(type(file)))
        if file.read(1) == '':
            return False
        elif max_size and len(file.read(max_size)) == max_size:
            raise Exception('file is too big')

        # beware of IE under win : need to get rid of filename path
        # and this is specific on client side
        # hack : try to see if it's a windows path
        # by searching ':/'
        file.filename = cleanUploadedFileName(file.filename)

        msg.attachFile(file)
        msg.setCachedValue('attacher_on', 0)
        if self.request is not None:
            self.request.response.redirect('editMessage.html')
            return None
        else:
            return True

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

    def saveMessageForm(self, **kw):
        """ saves the form into the message """
        if self.request is None:
            return False

        form = self.request.form

        EMPTY = '__#EMPTY#__'
        for key in form.keys():
            if form[key] == EMPTY:
                form[key] = ''

        for key in kw.keys():
            if kw[key] == EMPTY:
                form[key] = ''
            else:
                form[key] = kw[key]

        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()

        if form.has_key('msg_body'):
            msg_body = Utf8ToIso(form['msg_body'])
            msg.setDirectBody(msg_body)

        if form.has_key('msg_subject'):
            msg_subject = Utf8ToIso(form['msg_subject'])
            msg.setHeader('Subject', msg_subject)

        textareas = (('msg_to', 'To'), ('msg_cc', 'Cc'), ('msg_bcc', 'BCc'))

        for area, id in textareas:
            if form.has_key(area):
                msg_body = Utf8ToIso(form[area])
                """
                if msg_body.strip() == '':
                    continue
                """
                lines = msg_body.split('\n')
                msg.removeHeader(id)            # otherwise previous ones stays there
                for line in lines:
                    if line.strip() != '':
                        self.addRecipient(line, id, no_redirect=True)

        if form.has_key('cc_on'):
            msg.setCachedValue('cc_on', int(form['cc_on']))

        if form.has_key('bcc_on'):
            msg.setCachedValue('bcc_on', int(form['bcc_on']))

        if form.has_key('attacher_on'):
            msg.setCachedValue('attacher_on', int(form['attacher_on']))

        return 'cpsma_message_saved'

    def removeRecipient(self, value, type, redirect=''):
        """ removes a recipient """
        content = value.strip()
        if content == '':
            return
        if not type in('To', 'Cc', 'BCc'):
            type = 'To'
        mailbox = self.context
        msg = mailbox.getCurrentEditorMessage()

        msg.removeHeader(type, [value])

        if self.request is not None:
            if redirect is not None:
                self.request.response.redirect(redirect)
            else:
                self.request.response.redirect('editMessage.html')

    def addRecipient(self, content, type, no_redirect=False, redirect=None):
        """ add a recipient """
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

        if not no_redirect:
            if self.request is not None:
                if redirect is not None:
                    self.request.response.redirect(redirect)
                else:
                    self.request.response.redirect('editMessage.html')


    def editAction(self, **kw):
        """ dispatch a form action to the right method
        """
        if self.request is not None:
            if self.request.form is not None:
                for element in self.request.form.keys():
                    kw[element] = self.request.form[element]

        action = kw['action']

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

    def saveMessage(self, **kw):
        """ saves the message in Drafts """
        result = True
        mailbox = self.context

        if self.request is not None:
            self.saveMessageForm(**self.request.form)

        msg = mailbox.getCurrentEditorMessage()

        Tos = msg.getHeader('To')
        if Tos == [] or Tos == ['']:
            result = False
            psm = 'cpsma_message_saved_no_recipient'

        subject = msg.getHeader('Subject')
        if subject == [] or subject == ['']:
            result = False
            psm = 'cpsma_message_saved_no_subject'

        if result:
            msg_from = self._identyToMsgHeader()
            msg.setHeader('From', msg_from)
            mailbox.saveEditorMessage()
            psm = 'cpsma_message_saved'

        if self.request is not None:
            if 'responsetype' is not None:
                return result, psm
            else:
                self.request.response.redirect('editMessage.html?msm=%s' % psm)

        return None

    def initializeEditor(self, back_to_front=True, no_move=False):
        """ cleans the editor """
        mailbox = self.context
        mailbox.clearEditorMessage()
        if not no_move:
            if self.request is not None:
                if not back_to_front:
                    self.request.response.redirect('editMessage.html')
                else:
                    if hasattr(mailbox, 'INBOX'):
                        url = '%s/INBOX/view' % mailbox.absolute_url()
                    else:
                        url = '%s/view' % mailbox.absolute_url()
                    self.request.response.redirect(url)

    def toggleNotification(self):
        """ returns a notification """
        mailbox = self.context

        notification_header = 'Disposition-Notification-To'
        msg = mailbox.getCurrentEditorMessage()
        notification = msg.getHeader(notification_header)

        if notification == [] or notification is None:
            msg_from = self._identyToMsgHeader()
            msg.setHeader(notification_header, msg_from)
            result = True
        else:
            msg.removeHeader(notification_header)
            result = False

        if self.request is not None:
            if result:
                return 'cpsma_return_receipt'
            else:
                return ''
        else:
            return None

    def hasNotification(self):
        """ returns notification stats """
        mailbox = self.context
        notification_header = 'Disposition-Notification-To'
        msg = mailbox.getCurrentEditorMessage()
        notification = msg.getHeader(notification_header)

        result = not (notification == [] or notification is None)
        if self.request is not None:
            if result:
                return 'cpsma_return_receipt'
            else:
                return ''
        else:
            return result
