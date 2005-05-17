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
from email import message_from_string, Message
from email.MIMEText import MIMEText
from email import base64MIME
from email import Encoders
from email.Charset import Charset
from email.Header import decode_header

from zLOG import LOG, DEBUG, INFO
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from Products.Five import BrowserView
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem

from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from zope.app.cache.ram import RAMCache

from interfaces import IMailMessage, IMailFolder, IMailBox
from utils import decodeHeader, parseDateString, localizeDateString,\
                  secureUnicode
from mimeguess import mimeGuess
from mailrenderer import MailRenderer
from basemailview import BaseMailMessageView
from mailfolderview import MailFolderView

class MailMessage(Folder):
    """ Mailmessage is a lightweight message
        used for web manipulation
    """
    implements(IMailMessage)

    meta_type = "CPSMailAccess Message"

    _store = None
    instant_load = False
    seen = 0
    answered = 0
    deleted = 0
    flagged = 0
    forwarded = 0
    draft = 0
    size = 0
    junk = 0
    new = 0

    def __init__(self, id=None, uid='', digest='', **kw):
        Folder.__init__(self, id, **kw)
        self.uid = uid
        self.digest = digest
        self._file_list = []

    def loadMessageFromRaw(self, data):
        store = message_from_string(data)
        self._setStore(store)

    def _setStoreHeader(self, name, value):
        store = self._getStore()
        if store.has_key(name):
            del store[name]
        store[name] = value

    def loadMessage(self, flags=None, headers=None, body='',
                    structure_infos=None):
        if headers is not None:
            self._setStore(Message.Message())
        else:
            # this is a instant load,
            # getting back headers
            original_store = self._getStore()
            new_store = Message.Message()
            old_headers = ('From', 'To', 'Cc', 'Subject', 'Date', 'Message-ID',
                           'In-Reply-To', 'Content-Type')
            for old_header in old_headers:
                new_store[old_header] = original_store[old_header]
            self._setStore(new_store)

        store = self._getStore()
        # filling headers
        if structure_infos is not None:
            charset = 'ISO8859-15'
            for item in structure_infos:
                if isinstance(item, list):
                    if item[0] == 'charset':
                        charset = item[1]

            for item in structure_infos:
                if isinstance(item, list):
                    if item[0] == 'name':
                        self._setStoreHeader('name', item[1])

            content_type = '%s/%s' % (structure_infos[0], structure_infos[1])
            self._setStoreHeader('Content-type', content_type)

            if len(structure_infos) > 5:
                self._setStoreHeader('Content-transfer-encoding',
                                     structure_infos[4])
            else:
                self._setStoreHeader('Content-transfer-encoding', '')

            self._setStoreHeader('Charset', charset)
            skip_headers = ('content-type', 'content-transfer-encoding',
                            'charset')
        else:
            skip_headers = ()

        if headers is not None:
            for key in headers.keys():
                if key.lower() not in skip_headers:
                    if key.lower() == 'subject':
                        self.title = secureUnicode(decodeHeader(headers[key]))
                    self._setStoreHeader(key, headers[key])
        if body is None:
            body = ''

        store._payload = body
        #self._setStore(store)

        if flags is not None:
            self._parseFlags(flags)

    def getHeaders(self):
        """ Get a message headers """
        store = self._getStore()
        res = {}
        for header in store._headers:
            res[header[0]] = header[1]
        return res

    def _getStore(self):
        if self._store is None:
            self._store = Message.Message()
        return  self._store

    def _setStore(self, store):
        self._store = store

    def _parseFlags(self, flags):
        """ parses given raw flags """
        if isinstance(flags, list):
            flags = ' '.join(flags)
        flags = flags.lower()
        for item in ('seen', 'answered', 'deleted', 'flagged',
                     'forwarded', 'draft'):
            if flags.find(item) > -1:
                self.setFlag(item, 1)
            else:
                self.setFlag(item, 0)

    def setFlag(self, flag, value):
        """ sets a flag """
        if hasattr(self, flag):
            if getattr(self, flag) != value:
                setattr(self, flag, value)
                # call the event trigger
                self.onFlagChanged(self, flag, value)

    def getHeader(self, name):
        """ Get a message header. """
        store = self._getStore()

        elements = store.get_all(name, [])
        if elements is None:
            return []
        return elements

    def setHeader(self, name, value):
        """ Set a message header. """
        store = self._getStore()
        while store.has_key(name):
            # Erase previous header
            del store[name]
        store[name] = value

    def addHeader(self, name, value):
        """ adds an header """
        store = self._getStore()
        store[name] = value

    def removeHeader(self, name, values=None):
        """ removes header """
        store = self._getStore()
        headers = self.getHeader(name)
        if values is None:
            while store.has_key(name):
                # Erase previous header
                del store[name]
        else:
            for item in values:
                if item in headers:
                    headers.remove(item)
            if headers != values:
                while store.has_key(name):
                    # Erase previous header
                    del store[name]
                for value in headers:
                    self.addHeader(name, value)

    def setFlags(self, flags):
        flags = [flag.lower() for flag in flags]

        for flag in ('seen', 'answered', 'deleted', 'flagged',
                     'forwarded', 'draft'):
            if flag in flags:
                self.setFlag(flag, 1)
            else:
                self.setFlag(flag, 0)

    def onFlagChanged(self, msg, flag, value):
        """ can be used for event triggers """
        pass

    def getDirectBody(self):
        """ gets direct body """
        store = self._getStore()
        return store.get_payload()

    def getFlag(self, flag):
        """ gets a flag """
        return getattr(self, flag, None)

    def hasAttachment(self):
        """ tells if the message has an attachment """
        return len(self._file_list) > 0

    def getFileList(self):
        """ returns a filelist """
        # XXX todo
        return self._file_list

    def attachFile(self, file):
        """ attach an file """
        # XXXX not properly atatche, to be
        files = self._file_list
        exists =  False
        for cfile in files:
            if cfile['filename'] == file.filename:
                exists =  True
                break

        if not exists:
            file.seek(0)
            try:
                part_file = Message.Message()
                part_file['content-disposition'] = 'attachment; filename= %s'\
                        % file.filename
                part_file['content-transfer-encoding'] = 'base64'
                data = file.read()
                mime_type = mimeGuess(data)
                data = base64MIME.encode(data)
                part_file.set_payload(data)
                part_file['content-type'] = '%s; name=%s' % (mime_type,
                                                            file.filename)
            finally:
                file.close()

            file = {'filename' : file.filename, 'mimetype': mime_type,
                       'data' : part_file}

            files.append(file)

    def detachFile(self, filename):
        """ detach a file """
        files = self._file_list
        for i in range(len(files)):
            if files[i]['filename'] == filename:
                del files[i]
                break

    def setDirectBody(self, content):
        """ sets direct body content

        This is a facility for editor's need
        sets the first body content
        """
        store = self._getStore()
        store._payload = content


    def copyFrom(self, msg):
        """ make a copy (all but uid) """
        self.digest = msg.digest
        self._store = msg._store
        self.seen = msg.seen
        self.answered = msg.answered
        self.deleted = msg.deleted
        self.flagged = msg.flagged
        self.forwarded = msg.forwarded
        self.draft = msg.draft
        self.title = msg.title
        self._file_list = msg._file_list
        self.junk = msg.junk
        self.size = msg.size
        self.new = msg.new

    def getRawMessage(self):
        """ returns a raw message

        contains the store and eventually attached files
        """
        # XXX need to attach files in self._file_list
        store = self._getStore()
        if store is None:
            return ''
        else:
            # creating a mutlipart message
            copy = message_from_string(store.as_string())   # making a copy
            copy['content-type'] = 'text/plain; charset=iso-8859-1'
            copy['content-transfer-encoding'] = '7bits'

            if not self.hasAttachment:
                message = copy
            else:
                message = Message.Message()
                for gheader in ('From', 'To', 'Cc', 'BCc', 'Subject', 'Date',
                                'Return-Path', 'Received', 'Delivered-To',
                                'Message-ID'):
                    if copy[gheader] is not None:
                        message[gheader] = copy[gheader]
                        del copy[gheader]

                message['content-type'] = \
                    'multipart/mixed; boundary=---BOUNDARY---'
                message['MIME-version'] = '1.0'
                message._payload = [copy]

                # now appending files
                for file in self.getFileList():
                    # data contains the part
                    if file['data'] is not None:
                        message._payload.append(file['data'])

            message['User-Agent'] = 'Nuxeo CPSMailAccess'
            if message['Message-ID'] is None:
                # generate id XXXX need to be more precise here
                # by including user name
                folder = self.getMailFolder()
                if folder is None or folder.server_name=='':
                    key = '<%s>' % (self.uid)
                else:
                    key = '<%s.%s>' % (self.uid, folder.server_name)
                message['Message-ID'] = key
            return message.as_string()

    def getParams(self):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        return store.get_params()

    def getParam(self, param_name):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        return store.get_param(param_name)

    def setParam(self, param_name, param_value):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        store.set_param(param_name, param_value)

    def delParam(self, param_name):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        store.del_param(param_name)

    def getCharset(self):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        return store.get_charsets()[0]

    def getContentType(self):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        return store.get_content_type()

    def setCharset(self, charset):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        ob_charset = Charset(charset)
        store.set_charset(ob_charset)

    def setContentType(self, content_type):
        """ See interfaces.IMailMessage """
        store = self._getStore()
        store.set_type(content_type)

    def getMailFolder(self):
        """ gets parent folder
            XXX zope 2 style
        """
        if not hasattr(self, 'aq_inner'):
            return None
        return self.aq_inner.aq_parent

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
