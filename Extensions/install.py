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
""" Zope 2 style installer

"""
from zLOG import LOG, INFO, DEBUG
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.CPSInstaller.CPSInstaller import CPSInstaller
from OFS.ObjectManager import BadRequestException
from Products.CPSMailAccess.mailtool import manage_addMailTool

SKINS = {'cpsmailaccess_default' : 'Products/CPSMailAccess/skins',
         'cpsmailaccess_icons'   : 'Products/CPSMailAccess/skins/icons',
         'cpsmailaccess_mime_icons'   : 'Products/CPSMailAccess/skins/mime_icons',}

class CPSMailAccessInstaller(CPSInstaller):
    """ Installer class for CPSMailAccess
    """
    product_name = 'CPSMailAccess'

    def installProduct(self,ModuleName,
        InstallModuleName='install',MethodName='install'):
        """ creates an external method for a
            product install and launches it
        """
        objectName ="cpsmailaccess_"+ModuleName+"_installer"
        objectName = objectName.lower()
        # Install the product
        self.log(ModuleName+" INSTALL [ START ]")
        installer = ExternalMethod(objectName,
                                   "",
                                   ModuleName+"."+InstallModuleName,
                                   MethodName)
        try:
            self.portal._setObject(objectName,installer)

        except BadRequestException:
            self.log("External Method for "+ModuleName+" already installed")

        method_link = getattr(self.portal,objectName)
        method_link()
        self.log(ModuleName+" INSTALL [ STOP ]")

    def installProducts(self):
        """ install third party products
        """
        self.log("Installing TextIndexNG2...")
        #self.installProduct('TextIndexNG2', 'Install')
        self.log("... done")

    def install(self):
        """ make the installation
        """
        self.log("Install/Update : CPSMailAccess Product")
        self.installProducts()
        self.verifySkins(SKINS)
        self.setupPortalWebMail()
        self.setupTypes()
        self.setupBoxes()
        self.finalize()
        self.log("End of Install/Update : CPSMailAccess Product")

    def setupPortalWebMail(self):
        """ sets up portal webmail
        """
        # lets add a portal_webmail tool
        if not hasattr(self.portal, 'portal_webmail'):
            manage_addMailTool(self.portal)

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
                'btype': 'treeview',
                'box_skin': 'here/box_lib/macros/wbox',
                'slot': 'left',
                'order': 1,
                'display_in_subfolder': 1,
                'display_only_in_subfolder': 0,
                },
            'mailbox_actions': {
                'type': 'MailBoxTreeView',
                'title': 'MailBox Actions',
                'provider': 'mailaccess',
                'btype': 'actions',
                'box_skin': 'here/box_lib/macros/wbox',
                'slot': 'right',
                'order': 1,
                'display_in_subfolder': 1,
                'display_only_in_subfolder': 0,
                },
            'mailbox_attachedfiles': {
                'type': 'MailBoxTreeView',
                'title': 'MailBox Attached Files',
                'provider': 'mailaccess',
                'btype': 'attached_files',
                'box_skin': 'here/box_lib/macros/wbox',
                'slot': 'right',
                'order': 0,
                'display_in_subfolder': 1,
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
