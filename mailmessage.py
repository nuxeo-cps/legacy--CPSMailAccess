# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziad� <tz@nuxeo.com>
#          Florent Guillaume <tz@nuxeo.com>
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

from interfaces import IMailMessage, IMailMessageStore

from email import Message as Message
from email import message_from_string

class MailMessage(Folder):
    """A folderish mail 
    A MailMessage implements IMailMessage:
    >>> f = MailMessage()
    >>> IMailMessage.providedBy(f)
    True

    """
    implements(IMailMessage, IMailMessageStore)
    
    msg_uid = FieldProperty(IMailMessage['msg_uid'])    
    msg_key = FieldProperty(IMailMessage['msg_key'])
    
    store = None
    
    def __init__(self, id=None, msg_uid='', msg_key='', **kw):
        Folder.__init__(self, id, **kw)        
        self.msg_uid = msg_uid
        self.msg_key = msg_key
    
    def loadMessage(self, raw_msg):
        self.store = message_from_string(raw_msg)
        
""" classic Zope 2 interface for class registering
"""        
manage_addMailMessage = PageTemplateFile(
    "www/zmi_addmailmessage", globals(),
    __name__ = 'manage_addMailMessage')
    
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
    