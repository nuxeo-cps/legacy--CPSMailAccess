#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
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

from zLOG import LOG, INFO, DEBUG

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent

from Products.CPSInstaller.CPSInstaller import CPSInstaller

SKINS = {'cpsmailaccess_default' : 'Products/CPSMailAccess/skins',
         'cpsmailaccess_icons' : 'Products/CPSMailAccess/skins/icons',}

class CPSMailAccessInstaller(CPSInstaller):
    """ Installer class for CPSMailAccess
    """
    product_name = 'CPSMailAccess'

    def install(self):
        """ make the installation
        """
        self.log("Install/Update : CPSMailAccess Product")
        self.verifySkins(SKINS)
        self.setupPortalWebMail()
        self.setupTypes()
        self.setupBoxes()
        self.finalize()
        self.log("End of Install/Update : CPSMailAccess Product")

    def setupPortalWebMail(self):
        """ sets up portal webmail
        """
        pass

    def setupTypes(self):
        typestool = self.portal.portal_types
        namebox = 'MailBoxTreeView'
        ptypes_installed = typestool.objectIds()

        if namebox in ptypes_installed:
            typestool.manage_delObjects(namebox)
            self.log("  Type %s Deleted" % (namebox,))

        typestool.manage_addTypeInformation(id=namebox,
            add_meta_type='Factory-based Type Information',
            typeinfo_name='CPSMailAccess: MailBoxTreeView')

    def setupBoxes(self):
        """ sets up boxes
        """
        boxes = {
            'mailbox_treeview': {
                'type': 'MailBoxTreeView',
                'title': 'MailBox TreeView',
                'provider': 'mailaccess',
                'btype': 'default',
                'box_skin': 'here/box_lib/macros/wbox',
                'slot': 'left',
                'order': 3,
                'display_in_subfolder': 0,
                'display_only_in_subfolder': 0,
                },
        }
        self.verifyBoxes(boxes)

def install(self):
    """Installation is done here.

    Called by an external method for instance.
    """
    installer = CPSMailAccessInstaller(self)
    installer.install()
    return installer.logResult()
