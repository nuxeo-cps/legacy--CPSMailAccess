# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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
"""MailFolder

A MailFolder contains mail messages and other mail folders.
"""
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from interfaces import IMailMessage, IMailMessageStore, IMailMessageMapping
from email import Message as Message
from email import message_from_string
from email.Charset import Charset
from Globals import InitializeClass
from Products.Five import BrowserView
from mailrenderer import MailRenderer


class MailMessage(Folder):
    """A folderish mail
    A MailMessage implements IMailMessage:
    >>> f = MailMessage()
    >>> IMailMessage.providedBy(f)
    True

    """
    meta_type = "CPSMailAccess Message"

    implements(IMailMessage, IMailMessageStore, IMailMessageMapping)

    msg_uid = FieldProperty(IMailMessage['msg_uid'])
    msg_key = FieldProperty(IMailMessage['msg_key'])

    store = None

    def __init__(self, id=None, msg_uid='', msg_key='', **kw):
        Folder.__init__(self, id, **kw)
        self.msg_uid = msg_uid
        self.msg_key = msg_key

    def _getStore(self):
        """
        >>> f = MailMessage()
        >>> f.loadMessage('ok')
        >>> store = f._getStore()
        >>> store <> None
        True
        """
        if self.store is None:
            self.store = message_from_string('')

        return self.store


    def loadMessage(self, raw_msg):
        """ See interfaces.IMailMessage
        """
        self.store = message_from_string(raw_msg)

    def getPartCount(self):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if self.isMultipart():
            return len(store.get_payload())
        else:
            return 1

    def getPart(self, index=None, decode= False):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if index == None:
            try:
                part = store.get_payload(None, decode)
            except TypeError:
                part = None
        else:
            try:
                part = store.get_payload(index, decode)
            except TypeError:
                part = None

        return part


    def getCharset(self, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        return store.get_charsets()[part_index]

    def setCharset(self, charset, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        ob_charset = Charset(charset)

        if not self.isMultipart():
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_charset(ob_charset)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_charset(ob_charset)

    def isMultipart(self):
        """ See interfaces.IMailMessage
        >>> f = MailMessage()
        >>> f.loadMessage('mmdclkdshkdjg')
        >>> f.isMultipart()
        False
        """
        store = self._getStore()
        return store.is_multipart()

    def getContentType(self, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_content_type()
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_content_type()

    def setContentType(self, content_type, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_type(content_type)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_type(content_type)

    def getParams(self, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_params()
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_params()

    def getParam(self, param_name, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()

        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            return store.get_param(param_name)
        else:
            payload = store.get_payload()
            return payload[part_index-1].get_param(param_name)

    def setParam(self, param_name, param_value, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.set_param(param_name, param_value)
        else:
            payload = store.get_payload()
            payload[part_index-1].set_param(param_name, param_value)

    def delParam(self, param_name, part_index=0):
        """ See interfaces.IMailMessage
        """
        store = self._getStore()
        if not self.isMultipart() or part_index == 0:
            if part_index > 0:
                raise IndexError('Index out of bounds')
            store.del_param(param_name)
        else:
            payload = store.get_payload()
            payload[part_index-1].del_param(param_name)

    #
    # MAPPING INTERFACE (partial)
    #
    def __len__(self):
        """ see interface
        """
        store = self._getStore()
        return store.__len__()

    def __getitem__(self, name):
        """ see interface
        """
        store = self._getStore()
        return store.__getitem__(name)

    def __setitem__(self, name, val):
        """ see interface
        """
        # we want to override existing item if the
        # given value differs
        store = self._getStore()
        if store.has_key(name):
            if store[name] <> val:
                store.__delitem__(name)
        store.__setitem__(name, val)

    def __delitem__(self, name):
        """ see interface
        """
        store = self._getStore()
        store.__delitem__(name)

    def __contains__(self, name):
        """ see interface
        """
        store = self._getStore()
        return store.__contains__(name)

    def has_key(self, name):
        """ see interface
        """
        store = self._getStore()
        return store.has_key(name)

    def keys(self):
        """ see interface
        """
        store = self._getStore()
        return store.keys()

    def values(self):
        """ see interface
        """
        store = self._getStore()
        return store.values()

    def items(self):
        """ see interface
        """
        store = self._getStore()
        return store.items()

    def get(self, name, failobj=None):
        """ see interface
        """
        store = self._getStore()
        return store.get(name, failobj)

#
# MailMessage Views
#
class MailMessageView(BrowserView):

    _RenderEngine = MailRenderer()

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def _getSubject(self):
        if self.context is not None:
            subject = self.context['Subject']
            if subject is None:
                subject = '?'
        else:
            subject = '?'

        rendering = '<div id="mailSubject">' + subject + '</div>'

        return rendering

    def _getFromList(self):
        if self.context is not None:
            froms = self.context['From']
            if froms is None:
                froms = '?'
        else:
            froms = '?'

        rendering = '<div id="mailFrom">' + froms + '</div>'

        return rendering

    def _getToList(self):
        if self.context is not None:
            tos = self.context['To']
            if tos is None:
                tos = '?'
        else:
            tos = '?'

        rendering = '<div id="mailTo">' + tos + '</div>'

        return rendering

    def _bodyRender(self, mail, part_index):
        return self._RenderEngine.renderBody(mail, part_index)

    def _getBody(self):
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

        rendering = '<div id="mailBody">' + body + '</div>'

        return rendering


    def render(self):
        """ renders the mail
        """
        html = self._getSubject()
        #see if this is reliable
        html = html + '\n'
        html = html + self._getFromList()
        #see if this is reliable
        html = html + '\n'
        html = html + self._getToList()
        #see if this is reliable
        html = html + '\n'
        html = html + self._getBody()
        return html


""" classic Zope 2 interface for class registering
"""
InitializeClass(MailMessage)

manage_addMailMessageForm = PageTemplateFile(
    "www/zmi_addmailmessage", globals(),)

def manage_addMailMessage(container, id=None, msg_uid='',
        msg_key='', REQUEST=None, **kw):
    """Add a calendar to a container (self).
    >>> from OFS.Folder import Folder
    >>> f = Folder()
    >>> manage_addMailMessage(f, 'message')
    >>> f.message.getId()
    'message'

    """
    container = container.this()
    ob = MailMessage(id, msg_uid, msg_key, **kw)
    container._setObject(ob.getId(), ob)
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')
