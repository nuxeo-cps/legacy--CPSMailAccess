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

from zLOG import LOG, DEBUG, INFO
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from Products.Five import BrowserView
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem

from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from zope.app.cache.ram import RAMCache

from interfaces import IMailMessage, IMailFolder, IMailBox, IMailPart
from utils import decodeHeader, parseDateString, localizeDateString
from mimeguess import mimeGuess
from mailrenderer import MailRenderer
from basemailview import BaseMailMessageView
from mailpart import MailPart
from mailfolderview import MailFolderView

class MailMessage(MailPart):
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

    store = None
    sync_state = False

    read = 0
    answered = 0
    deleted = 0
    flagged = 0
    forwarded = 0
    draft = 0
    size = 0

    def __init__(self, id=None, uid='', digest='', **kw):
        Folder.__init__(self, id, **kw)
        self.uid = uid
        self.digest = digest
        self._cache = RAMCache()
        self.cache_level = 0

    def _addCache(self, key, data):
        """ to be extern. in mailfolder """
        if not hasattr(self, '_cache'):
            self._cache = RAMCache()
        self._cache.set(data, key)

    def _getCache(self, key):
        """ to be extern. in mailfolder """
        if not hasattr(self, '_cache'):
            self._cache = RAMCache()
            return None
        elements = self._cache.query(key)
        return elements


    def copyFrom(self, msg):
        """ make a copy (all but uid) """
        self.digest = msg.digest
        self.store = msg.store
        self.sync_state = msg.sync_state
        self.read = msg.read
        self.answered = msg.answered
        self.deleted = msg.deleted
        self.flagged = msg.flagged
        self.forwarded = msg.forwarded
        self.draft = msg.draft
        self.title = msg.title
        MailPart.copyFrom(self, msg)

    def setFlag(self, flag, value):
        """ sets a flag """
        if hasattr(self, flag):
            if getattr(self, flag) != value:
                setattr(self, flag, value)
                # call the event trigger
                self.onFlagChanged(self, flag, value)

    def onFlagChanged(self, msg, flag, value):
        """ can be used for event triggers """
        pass

    def getFlag(self, flag):
        """ gets a flag """
        return getattr(self, flag, None)

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
        """ Gets mailbox

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
            XXX zope 2 style
        """
        return self.aq_inner.aq_parent

    def getVolatilePart(self, part_name):
        """ gets volatile part """
        # keys *are* string
        part_name = str(part_name)
        return self._getCache(part_name)

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
        part = self.getVolatilePart(part_num)

        if part is not None:
            LOG('loadPart', INFO, 'i had it men')
            return part

        if part_num.find('.') == -1 and self.cache_level == 2:
            part_num_int = int(part_num)
            if part_num_int < self.getPartCount():
                part = self.getPart(part_num_int, True)
                if part is not None and part.get_payload() is not None:
                    return part

        LOG('loadPart - part', INFO, str(part))

        if part_content != '':
            part_str = part_content
            part = message_from_string(part_str)
        else:
            mailfolder = self.getMailFolder()
            connector = mailfolder._getconnector()
            if connector is not None:
                splitted = part_num.split('.')
                indexed = []
                for item in splitted:
                    indexed.append(int(item))

                raw_part = connector.getMessagePart(mailfolder.server_name,
                                                      self.uid, part_num)

                part_infos = connector.getPartInfos(mailfolder.server_name,
                                                    self.uid, indexed[0])

                LOG('loadPart - part_infos', INFO, str(part_infos))
                part = Message.Message()
                charset = 'ISO8859-15'
                for item in part_infos:
                    if isinstance(item, list):
                        if item[0] == 'charset':
                            charset = item[1]

                for item in part_infos:
                    if isinstance(item, list):
                        if item[0] == 'name':
                            part['name'] = item[1]

                part['Content-type'] = '%s/%s' % (part_infos[0], part_infos[1])
                part['Content-transfer-encoding'] = part_infos[4]
                part['Charset'] = charset
                part._payload = raw_part
                LOG('loadPart', INFO, 'got it from server %s !' % str(part_infos))

            else:
                part = None
                raise NotImplementedError

        if volatile:
            self._addCache(str(part_num), part)
            LOG('_addCache', INFO, 'saving it')
            return part
        else:
            ## todo : creates a real part
            raise NotImplementedError

    def loadMessage(self, raw_msg, cache_level=2):
        """ XXXX next we will
        implement here partial message load
        with part with None
        """
        self.cache_level = cache_level
        MailPart.loadMessage(self, raw_msg)
        self.title = decodeHeader(self._getStore()['Subject'])

    def detachFile(self, filename):
        """ detach a file """
        if not self.isMultipart():
            # it cant' be
            return False

        part_count = self.getPartCount()

        # we'll need to get back to a
        # simple string payload
        for part in range(part_count):
            part_ob = MailPart('part_'+str(part), self, self.getPart(part))
            infos = part_ob.getFileInfos()
            if infos is not None:
                if infos['filename'] == filename:
                    # founded
                    part_num = part
                    return self.deletePart(part_num)

        return False

    def attachFile(self, file):
        """ attach an file """
        file.seek(0)
        try:
            part_file = Message.Message()
            part_file['Content-Disposition'] = 'attachment; filename= %s'\
                       % file.filename
            part_file['Content-Transfer-Encoding'] = 'base64'
            data = file.read()
            mime_type = mimeGuess(data)
            data = base64MIME.encode(data)
            part_file.set_payload(data)
            part_file['Content-Type'] = '%s; name=%s' % (mime_type,
                                                         file.filename)
        finally:
            file.close()

        self.attachPart(part_file)

    def attachPart(self, part):
        """ attach an part """
        store = self._getStore()

        if not self.isMultipart():
            new_message = Message.Message()
            main_heads = ('date', 'to', 'from', 'cc', 'bcc')
            for header in self.getHeaders().keys():
                head = self.getHeader(header)
                for element in head:
                    if header.lower() not in main_heads:
                        new_message.add_header(header, element)
            new_message._payload = store._payload
            store._payload = [new_message]
            store['Content-Type'] = 'multipart/mixed; boundary="BOUNDARY"'

        store.attach(part)

    def hasAttachment(self):
        """ tells if the message has an attachment """
        if self.cache_level == 1:
            return False

        for part in range(self.getPartCount()):
            part_ob = MailPart('part_'+str(part), self, self.getPart(part))
            infos = part_ob.getFileInfos()
            if infos is not None:
                return True
        return False

    def setFlags(self, flags):
        flags = [flag.lower() for flag in flags]

        for flag in ('read', 'answered', 'deleted', 'flagged',
                     'forwarded', 'draft'):
            if flag in flags:
                self.setFlag(flag, 1)
            else:
                self.setFlag(flag, 0)

    def _parseFlags(self, flags):
        """ parses given raw flags """
        flags = flags.lower()
        for item in ('read', 'answered', 'deleted', 'flagged',
                     'forwarded', 'draft'):
            if flags.find(item) > -1:
                self.setFlag(item, 1)
            else:
                self.setFlag(item, 0)

    def setDirectBody(self, content):
        """ sets direct body content

        This is a facility for editor's need
        sets the first body content
        """
        if self.cache_level == 1:
            raise NotImplementedError

        if not self.isMultipart():
            self.setPart(0, content)
        else:
            # the mail editor message structure does not move
            sub = self.getPart(0)
            if isinstance(sub, str):
                self.setPart(0, content)
            else:
                sub._payload = content
                self.setPart(0, sub)

    def getDirectBody(self):
        """ gets direct body

        This is a facility for editor's need
        sets the first body content
        """
        if self.cache_level == 1:
            return ''

        try:
            res = self.getPart(0)
            if res is None:
                return ''
        except IndexError:
            res = ''

        if type(res) is str:
            return res
        else:
            return res.get_payload()

    def getPartCount(self):                                #XXXXXXXXXXXXXXXXX
        """ gets part count

        If cache is set to 1, this retrieves the structure
        on the server and count number of parts
        """
        if self.cache_level == 1:
            structure = self.getServerStructure()
            # counting parts
            # the first item is telling the type of structure
            if structure[0] not in ('relative', 'alteranive'):
                return 1
            return len(structure) - 1
        else:
            return MailPart.getPartCount(self)

    def getServerStructure(self):                        #XXXXXXXXXXXXXXXXX
        """ retrieves server structure """
        folder = self.getMailFolder()
        if folder is None:
            return []
        connector = folder._getconnector()
        server_name = folder.server_name
        return connector.getMessageStructure(server_name, self.uid)

    def isMultipart(self):                                #XXXXXXXXXXXXXXXXX
        """ gets part count

        If cache is set to 1, this retrieves the structure
        on the server and count number of parts totellif its multiparted
        """
        if self.cache_level == 1:
            part_count = self._getCache('part_count')
            if part_count is None:
                part_count = self.getPartCount()
                self._addCache('part_count', part_count)
            return part_count > 1
        else:
            return MailPart.isMultipart(self)

    def getContentType(self, part_index=0):
        if self.cache_level == 1:
            structure = self.getServerStructure()
            if isinstance(structure[1], list):
                return 'multipart/%s' % structure[0]
            else:
                return '%s/%s' % (structure[0], structure[1])
        else:
            return MailPart.getContentType(self, part_index)

    def getFileList(self):
        """ returns a filelist """
        files = []
        for part in range(self.getPartCount()):
            file = None
            if self.cache_level != 1:
                # XX todo : avoid re-generate part on each visit : use caching
                part_ob = MailPart('part_'+str(part), self, self.getPart(part))
                file = part_ob.getFileInfos()
            else:
                mailfolder = self.getMailFolder()
                if mailfolder is None:
                    return []
                connector = mailfolder._getconnector()

                infos = connector.getPartInfos(mailfolder.server_name,
                                               self.uid, part+1)
                for info in infos:
                    if isinstance(info, list):
                        list_ = info
                        if len(list_) == 2 and list_[0] == 'name':
                            file = {}
                            file['filename'] = list_[1]
                            file['mimetype'] = '%s/%s' % (infos[0], infos[1])

            if file is not None:
                file['part'] = part
                files.append(file)
        return files


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
