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
from email import message_from_string
from email import base64MIME
import thread
from urllib import quote

from zLOG import LOG, DEBUG, INFO
from Globals import InitializeClass
from Products.Five import BrowserView
from Products.Five.traversable import FiveTraversable
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

traverser_locker = thread.allocate_lock()

class MailTraverser(FiveTraversable):
    """ this is used to load message body when any
        view is called, because code that
        changes message in ZODB can't be called
        within a view, that might lead to conflict error
    """
    def traverse(self, name, furtherPath):
        """ taverser """
        mail = self._subject
        if mail.instant_load and name == 'view':
            traverser_locker.acquire()
            try:
                try:
                    mail._loadMessage()
                except ConnectionError:
                    # could not load
                    pass
            finally:
                traverser_locker.release()
        return FiveTraversable.traverse(self, name, furtherPath)

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
                date = u'?'
            else:
                date = decodeHeader(date[0])
        else:
            date = u'?'
        date = localizeDateString(date)
        return date

    def renderSmallDate(self):
        """ renders the mail date """
        context = self.context
        if context is not None: # and IMailPart.providedBy(context):
            date = self.context.getHeader('Date')
            if date == []:
                date = u'?'
            else:
                date = decodeHeader(date[0])
        else:
            date = u'?'
        date = localizeDateString(date, 3)
        return date

    def renderSubject(self):
        """ renders the mail subject """
        return self.renderHeaderList('Subject')

    def _renderLinkedHeaderList(self, name):
        list_ = self.renderHeaderList(name, True)
        root = self._getBoxRootUrl()
        final = []
        for mail in list_:
            dmail = mail.replace('<', '&lt;')
            dmail = dmail.replace('>', '&gt;')

            hmail = '<a href="%s/writeTo.html?msg_to=%s">%s</a>' %(root,
                                                                   quote(mail),
                                                                   dmail)
            final.append(hmail)

        return secureUnicode(u' '.join(final))

    def renderFromList(self):
        """ renders the mail From """
        return self._renderLinkedHeaderList('From')

    def renderToList(self):
        """ renders the mail list """
        return self._renderLinkedHeaderList('To')

    def renderCcList(self):
        """ renders the mail list """
        return self._renderLinkedHeaderList('Cc')

    def toCount(self):
        """ returns number of To recipients """
        return self.headerCount('To')

    def ccCount(self):
        """ returns number of Cc recipients """
        return self.headerCount('Cc')

    def fromCount(self):
        """ returns number of From recipients """
        return self.headerCount('From')

    def _removeNone(self, item):
        """ removes None """
        return item is not None

    def headerCount(self, name):
        """ tells the number of elements of a header """
        list_ = filter(self._removeNone, self.context.getHeader(name))
        return len(list_)

    def renderHeaderList(self, name, list_=False):
        """ renders the mail list """
        context = self.context
        if context is not None:# and IMailPart.providedBy(context):
            headers = self.context.getHeader(name)
            if headers == [] or headers is None:
                return u'?'
            else:
                decoded = []
                for header in headers:
                    if header is None:
                        continue
                    header = decodeHeader(header)
                    decoded.append(header)
                if len(decoded) == 0:
                    return u'?'
                if not list_:
                    return secureUnicode(u' '.join(decoded))
                else:
                    return decoded
        else:
            return u'?'

    def _bodyRender(self, mail):
        return self._RenderEngine.renderBody(mail)

    def _getBoxRootUrl(self):
        if self.context is not None:
            mail = self.context
            folder = mail.getMailFolder()
            if folder is None or not IMailFolder.providedBy(folder):
                root = ''
            else:
                box = folder.getMailBox()
                if box is None:
                    root = self.getAbsoluteUrl(folder)
                else:
                    root = self.getAbsoluteUrl(box)
            return root
        else:
            return ''

    def renderBody(self):
        """ renders the mail body """
        if self.context is not None:
            mail = self.context
            try:
                root = self._getBoxRootUrl()
                body = self._bodyRender(mail)
                mail_sub = r'<a href="%s/writeTo.html?msg_to=\1">\1</a>' % root
                body = linkifyMailBody(body, mail_sub)
            except NotImplementedError:
                body = 'cpsma_structure_unknown'
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

    def _setThreadHeader(self, message, origin):
        """ sets headers """
        message._generateMessageId()   # XXX to be outsourced
        if origin is not None:
            origin_id = origin.getHeader('Message-ID')
            if origin_id is not None and origin_id != []:
                message.addHeader('References', origin_id[0])
                message.setHeader('In-Reply-To', origin_id[0])

            references = origin.getHeader('References')
            if references is not None:
                hrefs = message.getHeader('References')
                for ref in references:
                    if ref not in hrefs:
                        message.addHeader('References', ref)

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

        # adding thread headers
        self._setThreadHeader(msg, origin_msg)

        if not forward:
            # adding from
            from_ = origin_msg.getHeader('From')[0]
            msg.addHeader('To', from_)

            msg.answerType = 'reply'
            froms = origin_msg.getHeader('From')
            for element in froms:
                if element is None:
                    continue
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
                if element is None:
                    continue
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

        msg.addHeader('Subject', answerSubject(subject, forward))

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
                           % (prefix, str(file['filename']))
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

    def notificationEmail(self):
        """ returns notification email if exists folder """
        message = self.context
        rendered = self.renderHeaderList('Disposition-Notification-To')
        if rendered == u'?':
            return None
        else:
            return rendered

    def notify(self, just_remove):
        """ returns a notification """
        recipient = self.notificationEmail()
        message = self.context
        # notify
        if just_remove != 1:
            result, error = self._sendNotification(recipient)
        else:
            result = True
            error = 'cpsma_notified'

        # remove header
        if recipient is not None and result:
            message.removeHeader('Disposition-Notification-To')
        return error

    def getunicodetext(self, message):
        """ retrieves a translation in a full unicode response """
        msg = self.context
        mailbox = msg.getMailBox()
        self.request.response.setHeader('content-type',
                                        'text/plain; charset=utf-8')
        if mailbox is not None:
            return translate(mailbox, message)
        else:
            return message

    def _sendNotification(self, recipient):
        """ sends a message """
        msg = self.context
        mailbox = msg.getMailBox()
        if mailbox is not None:
            try:
                return mailbox.sendNotification(recipient, msg)
            except ConnectionError:
                return False, 'cpsma_could_not_perform'
        else:
            return False, 'cpsma_no_mailbox'

    def getReferences(self):
        """ look in catalog for references """
        msg = self.context
        mailbox = msg.getMailBox()
        refs = mailbox.getReferences(msg)
        # we want to sort refs by dates
        sres = []
        for msg in refs:
            msg = traverseToObject(mailbox, msg)
            if msg is None:
                continue
            date = msg.getHeader('Date')
            if date != [] and date is not None:
                stDate = decodeHeader(date)
                sorter = parseDateString(stDate)
                sres.append((sorter, msg))
            else:
                sres.append(0, msg)
        sres.sort()
        return [item[1] for item in sres]

