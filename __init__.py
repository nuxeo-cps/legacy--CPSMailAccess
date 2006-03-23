#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
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

import os, sys

# add CPSMailAccess to the python path
product_dir = os.path.split(__file__)[0]
sys.path.insert(0, product_dir)

import permissions # for global role mapping

import mailbox
import mailfolder
import mailmessage
import mailtool
import mailboxtreeview
from interfaces import IMailTool

## XXX dependencies introduced by the box creation
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.utils import ContentInit
try:
    from Products.CMFCore.permissions import AddPortalContent
except ImportError:
    # BBB for CMF 1.4, remove this in CPS 3.4.0
    from Products.CMFCore.CMFCorePermissions import AddPortalContent

from Products.GenericSetup import EXTENSION
from Products.GenericSetup import profile_registry

from Products.CPSCore.interfaces import ICPSSite

contentClasses = (mailboxtreeview.MailBoxTreeView, )
contentConstructors = (mailboxtreeview.manage_addMailBoxTreeview, )
fti = (mailboxtreeview.factory_type_information + ())

registerDirectory('skins', globals())

def initialize(context):
    context.registerClass(
        mailbox.MailBox,
        constructors = (mailbox.manage_addMailBoxForm,
                        mailbox.manage_addMailBox),
        )

    context.registerClass(
        mailfolder.MailFolder,
        constructors = (mailfolder.manage_addMailFolderForm,
                        mailfolder.manage_addMailFolder),
        )

    context.registerClass(
        mailmessage.MailMessage,
        constructors = (mailmessage.manage_addMailMessageForm,
                        mailmessage.manage_addMailMessage),
        )

    context.registerClass(
        mailtool.MailTool,
        constructors = (mailtool.manage_addMailToolForm,
                        mailtool.manage_addMailTool),
        )

    ContentInit('MailBoxTreeView',
                content_types = contentClasses,
                permission = AddPortalContent,
                extra_constructors = contentConstructors,
                fti = fti).initialize(context)

    profile_registry.registerProfile('default',
                                     'CPS MailAccess',
                                     "Profile for CPSMailAccess.",
                                     'profiles/default',
                                     'CPSMailAccess',
                                     EXTENSION,
                                     for_=ICPSSite)
