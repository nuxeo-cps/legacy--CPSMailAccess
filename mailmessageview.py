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
from email import message_from_string
from email import base64MIME

from zLOG import LOG, DEBUG, INFO
from Globals import InitializeClass
from Products.Five import BrowserView
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem

from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty

from interfaces import IMailMessage, IMailFolder, IMailBox
from baseconnection import ConnectionError
from mailrenderer import MailRenderer
from basemailview import BaseMailMessageView
from mailfolderview import MailFolderView
from mailexceptions import MailPartError
from utils import *


class MailMessageView(BaseMailMessageView):

    _RenderEngine = MailRenderer()
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def renderDate(self):
        """ renders the mail date """
        context = self.context
        if context is not None: # and IMailPart.providedBy(context):
            date = self.context.getHeader('Date')
            if date == []:
                date = '?'
            else:
                date = decodeHeader(date[0])
        else:
            date = '?'
        date = localizeDateString(date)
        return date

    def renderSmallDate(self):
        """ renders the mail date """
        context = self.context
        if context is not None: # and IMailPart.providedBy(context):
            date = self.context.getHeader('Date')
            if date == []:
                date = '?'
            else:
                date = decodeHeader(date[0])
        else:
            date = '?'
        date = localizeDateString(date, 3)
        return date

    def renderSubject(self):
        """ renders the mail subject """
        return self.renderHeaderList('Subject')

    def renderFromList(self):
        """ renders the mail From """
        return self.renderHeaderList('From')

    def renderToList(self):
        """ renders the mail list """
        return self.renderHeaderList('To')

    def renderCcList(self):
        """ renders the mail list """
        return self.renderHeaderList('Cc')

    def toCount(self):
        """ returns number of To recipients """
        return self.headerCount('To')

    def ccCount(self):
        """ returns number of Cc recipients """
        return self.headerCount('Cc')

    def fromCount(self):
        """ returns number of From recipients """
        return self.headerCount('From')

    def headerCount(self, name):
        """ tells the number of elements of a header """
        return len(self.context.getHeader(name))

    def renderHeaderList(self, name):
        """ renders the mail list """
        context = self.context
        if context is not None:# and IMailPart.providedBy(context):
            headers = self.context.getHeader(name)
            if headers == []:
                return u'?'
            else:
                decoded = []
                for header in headers:
                    header = decodeHeader(header)
                    decoded.append(header)
                return u' '.join(decoded)
        else:
            return u'?'

    def _bodyRender(self, mail):
        return self._RenderEngine.renderBody(mail)

    def renderBody(self):
        """ renders the mail body """
        if self.context is not None:
            mail = self.context
            # the user reads the messge, let's
            # sets the read message to 1
            if mail.getFlag('seen') == 0:
                mail.setFlag('seen', 1)
                folder = mail.getMailFolder()
                if folder is not None:
                    folder.onFlagChanged(mail, 'seen', 1)
            if mail.instant_load:
                # loading mail on-the fly
                # xxx todo: outsource this
                folder = mail.getMailFolder()
                if folder is not None:
                    server_name = folder.server_name
                    uid = mail.uid
                    connector = folder._getconnector()
                    folder._loadMessageStructureFromServer(server_name, uid,
                                                           None, None, None,
                                                           mail, connector,
                                                           afterload=True)

            body = self._bodyRender(mail)
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

    def prepareReplyRecipient(self, reply_all=0, forward=0):
        """ prepare msg recipient """
        origin_msg = self.context
        mailbox = origin_msg.getMailBox()
        body_value = self.renderBody()
        from_value = self.renderFromList()
        reply_content = replyToBody(from_value, body_value)
        mailbox.clearEditorMessage()
        msg = mailbox.getCurrentEditorMessage()
        msg.setDirectBody(reply_content)
        recipients = []
        msg.origin_message = origin_msg

        if not forward:
            # adding from
            from_ = origin_msg.getHeader('From')[0]
            msg.addHeader('To', from_)

            msg.answerType = 'reply'
            froms = origin_msg.getHeader('From')
            for element in froms:
                if element not in recipients:
                    recipients.append(element)
        else:
            msg.answerType = 'forward'

        if reply_all and not forward:
            ccs = origin_msg.getHeader('Cc')
            tos = origin_msg.getHeader('To')
            boxmail = self._getBoxMail()
            # cc -> cc
            # to -> cc if to is different than boxmail
            for to in tos:
                if sameMail(boxmail, to):
                    del tos[to]
            ccs.extend(tos)

            for element in ccs:
                msg.addHeader('Cc', element)

        if not reply_all and forward:
            # todo : append attached files
            # XXX to be done
            """
            for part in range(origin_msg.getPartCount()):
                # XX todo : avoid re-generate part on each visit : use caching
                current_part = origin_msg.getPart(part)
                part_ob = MailPart('part_'+str(part), origin_msg, current_part)
                infos = part_ob.getFileInfos()
                if infos is not None:
                    msg.attachPart(current_part)
            """
            pass

        subjects = origin_msg.getHeader('Subject')
        if subjects == []:
            subject = ''
        else:
            subject = subjects[0]

        if not forward:
            msg.addHeader('Subject', 'Re: ' + subject)
        else:
            msg.addHeader('Subject', 'Fwd: '+ subject)

        if self.request is not None:
            came_from = origin_msg.absolute_url()
            self.request.response.redirect('%s/editMessage.html?came_from=%s' \
                % (mailbox.absolute_url(), came_from))

    def reply(self):
        """ replying to a message """
        self.prepareReplyRecipient(reply_all=0, forward=0)

    def reply_all(self):
        """ replying to a message """
        self.prepareReplyRecipient(reply_all=1, forward=0)

    def forward(self):
        """ forwarding a message """
        self.prepareReplyRecipient(reply_all=0, forward=1)

    def delete(self):
        """ "deletes" the message

        Copy it to the thrash in fact
        """
        mailbox = self.context.getMailBox()
        msg = self.context
        msg_container = msg.getMailFolder()
        trash_folder = mailbox.getTrashFolder()
        # deletes it locally *and* from server
        msg_container.moveMessage(msg.uid, trash_folder)
        # need to do the same on server
        msg.setFlag('deleted', 1)
        if msg_container is not None:
            msg_container.onFlagChanged(msg, 'deleted', 1)

        if self.request is not None:
            psm = 'Message sent to Trash.'
            folder = msg_container.absolute_url()
            self.request.response.\
                redirect('%s/view?msm=%s' % (folder, psm))

    def attached_files(self):
        # todo :scans attached files
        message = self.context
        # XX hack : need to do better
        if hasattr(message, 'editor_msg'):
            prefix = 'editorMessage'
        else:
            prefix = message.absolute_url()

        files = message.getFileList()
        list_files = []

        for file in files:
            file['url'] = '%s/viewFile.html?filename=%s' \
                    %(prefix, str(file['filename']))
            file['icon'] =  mimetype_to_icon_name(file['mimetype'])
            file['fulltitle'] = file['filename']
            file['title'] = file['filename']
            file['delete_url'] = ('deleteAttachement.html?filename=' +
                                  file['filename'])
            list_files.append(file)

        i = 0
        clist_files = []
        while i < len(list_files):
            if i+1 < len(list_files):
                clist_files.append([list_files[i], list_files[i+1]])
            else:
                clist_files.append([list_files[i]])
            i += 2
        return clist_files

    def _getMailFile(self, mail, part):
        """ mailfile """
        mailfolder = mail.getMailFolder()
        if mailfolder is None:
            return None
        else:
            uid = mail.uid
            return mailfolder.getMessagePart(uid, part)

    def viewFile(self, filename):
        """ returns a file """
        mail = self.context
        files = mail.getFileList()
        found = False
        for file in files:
            if file['filename'] == filename:
                data = file['data']
                if data is None:
                    data = self._getMailFile(mail, file['part'])

                filecontent = data
                cte = file['content-transfer-encoding']

                content_type = file['mimetype']
                if isinstance(cte, list):
                    if cte != []:
                        cte = cte[0]
                    else:
                        cte ='7bit'

                if cte == 'base64':
                    filecontent = base64MIME.decode(filecontent)
                found = True

        if not found:
            return None
        else:
            if self.request is not None:
                response = self.request.response
                response.setHeader('Content-Type', content_type)
                response.setHeader('Content-Disposition', 'inline; filename=%s' % filename)
                response.setHeader('Content-Length', len(filecontent))
                response.write(filecontent)

            return filecontent

    def reload(self):
        """ reloads a message to mail editor """
        message = self.context
        box = message.getMailBox()

        box.setCurrentEditorMessage(message)

        if self.request is not None:
           response = self.request.response
           url = box.absolute_url()
           response.redirect('%s/editMessage.html' % url)

    def _getBoxMail(self):
        """ returns the box email

        this is used to find the mail in To/Cc lists
        """
        message = self.context
        box = message.getMailBox()
        return box.getIdentitites()[0]['email']

    def getMessageListCols(self):
        """ returns the list of cols """
        message = self.context
        mailbox = message.getMailBox()
        list_cols = mailbox.getConnectionParams()['message_list_cols']
        if isinstance(list_cols, str):
            list_cols = [item.strip() for item in list_cols.split(',')]
        return list_cols

    def getMailFolder(self):
        """ returns mail folder """
        message = self.context
        return message.getMailFolder()


