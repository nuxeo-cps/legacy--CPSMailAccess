# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziadé <tz@nuxeo.com>
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
"""MailBox

A MailBox is the root MailFolder for a given mail account
"""
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder

from zope.schema.fieldproperty import FieldProperty
from zope.app import zapi
from zope.interface import implements

from utils import uniqueId, makeId
from Products.CPSMailAccess.interfaces import IMailBox
from Products.CPSMailAccess.mailfolder import MailFolder

from interfaces import IMailFolder, IMailMessage

class MailBox(MailFolder):
    """ the main container

    >>> f = MailBox()
    >>> IMailFolder.providedBy(f)    
    True
    >>> IMailBox.providedBy(f)
    True
    """    
    implements(IMailBox)
    
    def __init__(self, uid=None, server_name='', **kw):
        MailFolder.__init__(self, uid, server_name, **kw)    
          
        
                           
""" classic Zope 2 interface for class registering
"""        
manage_addMailBox = PageTemplateFile(
    "www/zmi_addmailbox", globals(),
    __name__ = 'manage_addMailBox')
    
def manage_addMailBox(container, id=None, server_name ='', 
        REQUEST=None, **kw):
    """Add a box to a container (self).
    >>> from OFS.Folder import Folder
    >>> f = Folder()
    >>> manage_addMailBox(f, 'mails')
    >>> f.mails.getId()
    'mails'
    """
    container = container.this()
    ob = MailBox(id, server_name, **kw)
    container._setObject(ob.getId(), ob)
    if REQUEST is not None:
        ob = container._getOb(ob.getId())
        REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_main')
        