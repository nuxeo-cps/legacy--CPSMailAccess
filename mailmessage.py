# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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
"""MailMessage

A MailMessage is an individual message from the server.
"""
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from interfaces import IMailMessage, IMailFolder, IMailBox, IMailPart
from utils import decodeHeader
from Globals import InitializeClass
from Products.Five import BrowserView
from mailrenderer import MailRenderer
from basemailview import BaseMailMessageView
from mailpart import MailPart
from email import message_from_string

## XX todo : need to add a setPart to add parts on the fly

class MailMessage(Folder, MailPart):
    """A mail message.

    A mail message wraps an email.Message object.
    It makes its subparts accessible as subobjects.

    It may be incomplete: some parts may be missing (None).
    XXX still unclear whose responsibility it is to fetch missing parts.

    A MailMessage implements IMailMessage:
    >>> f = MailMessage()
    >>> IMailMessage.providedBy(f)
    True
    >>> IMailPart.providedBy(f)
    True
    """
    implements(IMailMessage, IMailPart)
    meta_type = "CPSMailAccess Message"

    uid = '' # server uid
    digest = ''
    store = None
    sync_state = False

    _v_volatile_parts = {}

    def __init__(self, id=None, uid='', digest='', **kw):
        Folder.__init__(self, id, **kw)
        self.uid = uid
        self.digest = digest

    def setSyncState(self, state=False):
        """ sets state
        """
        self.sync_state = state

    def _getStore(self):
        """
        >>> f = MailMessage()
        >>> f.cache_level = 0
        >>> f.loadMessage('ok')
        >>> store = f._getStore()
        >>> store <> None
        True
        """
        if self.store is None:
            self.cache_level = 0
            self.loadMessage('')
        return self.store

    def _setStore(self, store):
        self.store = store

    def getMailBox(self):
        """ gets mailbox
            XXXX might be kicked out in utils so
            there's no dependencies with MailBox
        """
        parent_folder = self.getMailFolder()
        if parent_folder is None:
            return None
        else:
            if IMailBox.providedBy(parent_folder):
                return parent_folder
            else:
                return parent_folder.getMailBox()

    def getMailFolder(self):
        """ gets parent folder
        """
        return self.aq_inner.aq_parent

    def loadPart(self, part_num, part_content='', volatile=True):
        """ loads a part in the volatile list
            or in the persistent one
            if part_content is empty,fetching the server
        """
        # XXXX still unclear if this is the right place
        # to do so
        # this api has to be used for the primary load
        # optimization = if the part is already here *never*
        # reloads it, it has to be cleared if reload is needed somehow
        part_num_str = str(part_num)

        if self._v_volatile_parts.has_key(part_num_str):
            return self._v_volatile_parts[part_num_str]

        if part_num < self.getPartCount():
            part = self.getPart(part_num)
            if part is not None:
                return part

        if part_content != '':
            part_str = part_content
        else:
            mailfolder = self.getMailFolder()
            connector = mailfolder._getconnector()

            if connector is not None:
                part_str = connector.fetchPartial(mailfolder.server_name, self.uid,
                    part_num, 0, 0)

        part = message_from_string(part_str)
        if volatile:
            self._v_volatile_parts[str(part_num)] = part
        else:
            ## todo : creates a real part
            raise 'todo create a real part here'



#
# MailMessage Views
#
class MailMessageView(BaseMailMessageView):

    _RenderEngine = MailRenderer()

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

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
            if mail.isMultipart():
                ### XXXXXX todo here : recursively parse multipart
                ### messages
                body = self._bodyRender(mail, 0)
                # XXXXXXXXXXhere we need part parsing

                #raise str(body)
            else:
                body = ''
                if mail.getPartCount() > 0 :
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

        returned = []
        elements = mailfolder.getMailMessages(list_folder=False,
            list_messages=True, recursive=False)

        for element in elements:
            part = {}
            part['object'] = element
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
            part['Date'] = decodeHeader(element_date)

            returned.append(part)
        return returned

    def reply(self):
        """ replying to a message
            is writing a message with a given "to" "from"
            and with a given body
        """
        # getting mailbox
        # Zope 2 code, need to put in in utils
        mailbox = self.context.getMailBox()

        if self.request is not None:
            self.request.form['came_from'] = self.context.absolute_url()
            self.request.response.redirect('%s/editMessage.html' % mailbox.absolute_url())

    def reply_all(self):
        """ replying to a message
            is writing a message with a given "to" "from"
            and with a given body
        """
        # getting mailbox
        # Zope 2 code, need to put in in utils
        mailbox = self.context.getMailBox()

        if self.request is not None:
            self.request.form['came_from'] = self.context.absolute_url()
            self.request.response.redirect('%s/editMessage.html' % mailbox.absolute_url())

    def forward(self):
        """ replying to a message
            is writing a message with a given "to" "from"
            and with a given body
        """
        # getting mailbox
        # Zope 2 code, need to put in in utils
        mailbox = self.context.getMailBox()

        if self.request is not None:
            self.request.form['came_from'] = self.context.absolute_url()
            self.request.response.redirect('%s/editMessage.html' % mailbox.absolute_url())

    def delete(self):
        pass

""" classic Zope 2 interface for class registering
"""
InitializeClass(MailMessage)

manage_addMailMessageForm = PageTemplateFile(
    "www/zmi_addmailmessage", globals(),)

def manage_addMailMessage(container, id=None, uid='',
        digest='', REQUEST=None, **kw):
    """Add a mailmessage to a container (self).
    >>> from OFS.Folder import Folder
    >>> f = Folder()
    >>> manage_addMailMessage(f, 'message')
    >>> f.message.getId()
    'message'

    """
    container = container.this()
    ob = MailMessage(id, uid, digest, **kw)
    container._setObject(ob.getId(), ob)
    if IMailFolder.providedBy(container):
        container.message_count += 1
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')