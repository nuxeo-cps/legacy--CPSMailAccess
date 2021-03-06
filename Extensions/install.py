#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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
import os
from OFS.ObjectManager import BadRequestException

from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.CMFCore.utils import getToolByName
from Products.CPSInstaller.CPSInstaller import CPSInstaller
from Products.CPSMailAccess.mailtool import manage_addMailTool,\
                                            default_parameters
from Products.CPSMailAccess.permissions import permissions
from Products.CPSMailAccess.mailbox import MailBox

# XXX AT: is it a test on CPSSubscriptions presence/install?
try:
  from Products.CPSSubscriptions.permissions import CanNotifyContent
  CPSSubscriptions = 1
except ImportError:
  CPSSubscriptions = 0


SKINS = {'cpsmailaccess_default' : 'Products/CPSMailAccess/skins',
         'cpsmailaccess_icons'   : 'Products/CPSMailAccess/skins/icons',
         'cpsmailaccess_mime_icons'   : 'Products/CPSMailAccess/skins/mime_icons',}

class CPSMailAccessInstaller(CPSInstaller):
    """ Installer class for CPSMailAccess
    """
    product_name = 'CPSMailAccess'
    _versions = [(1, 0, 0, 'b1'), (1, 0, 0, 'b2')]

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

    def install(self):
        """ make the installation
        """
        self.log("Install/Update : CPSMailAccess Product")
        self.verifySkins(SKINS)
        self.resetSkinCache()
        self.setupPortalWebMail()
        self.setupTypes()
        self.setupBoxesorPortlets()
        self.setupDefaultAddressBooks()
        self.setupMembersSchemasAndLayouts()
        self.addWMAction()
        self.setupPermissions()
        # XXX not used yet
        # self.linkFiveActionTool()
        self.setupTranslations()
        self.finalize()
        self.log("End of Install/Update : CPSMailAccess Product")

    def setupPortalWebMail(self):
        """ sets up portal webmail
        """
        # lets add a portal_webmail tool
        if not hasattr(self.portal, 'portal_webmail'):
            manage_addMailTool(self.portal)
        else:
            # seems to be already installed,
            # let's try to upgrade its parameters
            self.upgrade_parameters()

    def setupTypes(self):
        typestool = self.portal.portal_types
        namebox = 'MailBoxTreeView'
        ptypes_installed = typestool.objectIds()

        if namebox in ptypes_installed:
            typestool.manage_delObjects(namebox)
            self.log("  Type %s Deleted" % (namebox,))

        from zExceptions import BadRequest
        add_meta_type='Factory-based Type Information'
        typeinfo_name='CPSMailAccess: MailBoxTreeView'

        try:
            typestool.manage_addTypeInformation(id=namebox,
                                                add_meta_type=add_meta_type,
                                                typeinfo_name=typeinfo_name)
        except BadRequest:
            # CMF new-style notation
            typeinfo_name = \
                'CPSMailAccess: portal_type_MailBoxTreeView_title(MailBoxTreeView)'
            typestool.manage_addTypeInformation(id=namebox,
                                                add_meta_type=add_meta_type,
                                                typeinfo_name=typeinfo_name)

    def setupBoxes(self):
        """ sets up boxes """
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

    def setupDefaultAddressBooks(self):
        """ sets up adress books
        """

        self.log(" Setting up default address book directories")
        addressbook_directory = {
            'type': 'CPS ZODB Directory',
            'data': {
                'title': 'label_address_book',
                'schema': 'addressbook',
                'schema_search': 'addressbook_search',
                'layout': 'addressbook',
                'layout_search': 'addressbook_search',
                'acl_directory_view_roles': 'Manager; Member',
                'acl_entry_create_roles': 'Manager',
                'acl_entry_delete_roles': 'Manager',
                'acl_entry_view_roles': 'Manager; Member',
                'acl_entry_edit_roles': 'Manager',
                'id_field': 'id',
                'title_field': 'fullname',
                'search_substring_fields': ['fullname', 'email', 'id', 'sn'],
                },
            }

        privaddressbook_directory = {
            'type': 'CPS Local Directory',
            'data': {
                'title': 'label_personal_addressbook',
                'schema': 'addressbook',
                'schema_search': 'addressbook_search',
                'layout': 'addressbook',
                'layout_search': 'addressbook_search',
                'acl_directory_view_roles': 'Manager; Member',
                'acl_entry_create_roles': 'Manager; Member',
                'acl_entry_delete_roles': 'Manager; Member',
                'acl_entry_view_roles': 'Manager; Member',
                'acl_entry_edit_roles': 'Manager; Member',
                'id_field': 'id',
                'title_field': 'fullname',
                'search_substring_fields': ['fullname', 'email', 'id', 'sn'],
                'directory_ids': [],
                'directory_type': 'CPS ZODB Directory',
                },
            }

        directories = {
            'addressbook': addressbook_directory,
            '.addressbook': privaddressbook_directory
            }

        self.verifyDirectories(directories)

        self.log("Address book directories added")

        portal = self.portal

        addressbook_schema = {
            'email': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'fullname': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    'read_ignore_storage': 1,
                    # sometimes crashes if there is no call to str()
                    'read_process_expr': """python:(givenName + " " + sn).strip()""",
                    'read_process_dependent_fields': ('givenName', 'sn', 'id'),
                    'write_ignore_storage': 1,
                    },
                },
            'id': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'givenName': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'sn': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'mails_sent': {
                    'type': 'CPS Int Field',
                    'data': {
                        'default_expr': 'python:0',
                    },
                },
            }

        addressbook_search_schema = {
            'email': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'id': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'givenName': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'sn': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            }

        schemas = {
            'addressbook': addressbook_schema,
            'addressbook_search': addressbook_search_schema,
            }
        self.verifySchemas(schemas)

        addressbook_layout = {
            'widgets': {
                'fullname': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('fullname',),
                        'is_required': 0,
                        'label': 'label_full_name',
                        'label_edit': 'label_full_name',
                        'is_i18n': 1,
                        'hidden_layout_modes': ('create', 'edit', 'search'),
                        'display_width': 30,
                        'size_max': 0,
                        },
                    },
                'id': {
                    'type': 'Identifier Widget',
                    'data': {
                        'fields': ('id',),
                        'is_required': 1,
                        'label': 'label_user_name',
                        'label_edit': 'label_user_name',
                        'is_i18n': 1,
                        'readonly_layout_modes': ('edit',),
                        'display_width': 30,
                        'size_max': 256,
                        },
                    },
                'givenName': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('givenName',),
                        'is_required': 0,
                        'label': 'label_first_name',
                        'label_edit': 'label_first_name',
                        'is_i18n': 1,
                        'display_width': 20,
                        'size_max': 0,
                        },
                    },
                'sn': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('sn',),
                        'is_required': 0,
                        'label': 'label_last_name',
                        'label_edit': 'label_last_name',
                        'is_i18n': 1,
                        'display_width': 20,
                        'size_max': 0,
                        },
                    },
                'email': {
                    'type': 'Email Widget',
                    'data': {
                        'fields': ('email',),
                        'is_required': 0,
                        'label': 'label_email',
                        'label_edit': 'label_email',
                        'is_i18n': 1,
                        'display_width': 30,
                        'size_max': 0,
                        },
                    },
                },
            'layout': {
                'style_prefix': 'layout_dir_',
                'flexible_widgets': [],
                'ncols': 2,
                'rows': [
                    [{'ncols': 2, 'widget_id': 'id'},
                     ],
                    [{'ncols': 2, 'widget_id': 'fullname'},
                     ],
                    [{'ncols': 2, 'widget_id': 'email'},
                     ],
                    [{'ncols': 2, 'widget_id': 'givenName'},
                     ],
                    [{'ncols': 2, 'widget_id': 'sn'},
                     ],
                    ],
                },
            }

        addressbook_search_layout = {
            'widgets': {
                'id': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('id',),
                        'is_required': 0,
                        'label': 'label_user_name',
                        'label_edit': 'label_user_name',
                        'is_i18n': 1,
                        'readonly_layout_modes': ('edit',),
                        'display_width': 20,
                        'size_max': 0,
                        },
                    },
                'givenName': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('givenName',),
                        'is_required': 0,
                        'label': 'label_first_name',
                        'label_edit': 'label_first_name',
                        'is_i18n': 1,
                        'display_width': 20,
                        'size_max': 0,
                        },
                    },
                'sn': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('sn',),
                        'is_required': 0,
                        'label': 'label_last_name',
                        'label_edit': 'label_last_name',
                        'is_i18n': 1,
                        'display_width': 20,
                        'size_max': 0,
                        },
                    },
                'email': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('email',),
                        'is_required': 0,
                        'label': 'label_email',
                        'label_edit': 'label_email',
                        'is_i18n': 1,
                        'display_width': 30,
                        'size_max': 0,
                        },
                    },
                },
            'layout': {
                'style_prefix': 'layout_dir_',
                'flexible_widgets': [],
                'ncols': 2,
                'rows': [
                    [{'ncols': 2, 'widget_id': 'id'},
                     ],
                    [{'ncols': 2, 'widget_id': 'email'},
                     ],
                    [{'ncols': 2, 'widget_id': 'givenName'},
                     ],
                    [{'ncols': 2, 'widget_id': 'sn'},
                     ],
                    ],
                },
            }

        layouts = {
            'addressbook': addressbook_layout,
            'addressbook_search': addressbook_search_layout,
            }
        self.verifyLayouts(layouts)


    def setupMembersSchemasAndLayouts(self):
        """ adds a checkbox that tells if the user
            has webmail capabilities
            (for a default configuration)
        """
        self.log(" Setting up schemas and layouts")
        portal = self.portal
        stool = portal.portal_schemas
        memberschema = stool.members
        existing_fields = memberschema.objectIds()
        pmd = portal.portal_memberdata

        fields = [('webmail_enabled', 'CPS Int Field', 'int',
                   'Boolean Widget', 'python:0'),]

        for field in fields:
            if not 'f__%s' % field[0] in existing_fields:
                memberschema.addField(field[0], field[1],
                                      acl_write_roles_str='Manager, Owner',
                                      default_expr=field[4])

            if not pmd.hasProperty(field[0]):
                pmd.manage_addProperty(field[0], 0, field[2])

        ltool = portal.portal_layouts
        memberlayout = ltool.members
        widgets = memberlayout.objectIds()
        layout_def = memberlayout.getLayoutDefinition()

        for field in fields:
            if not 'w__%s' % field[0] in widgets:
                memberlayout.addWidget(field[0], field[3],
                                    fields=field[0],
                                    label='label_%s' % field[0],
                                    label_edit='label_%s' % field[0],
                                    is_i18n=1,
                                    )
                rows = layout_def['rows']
                exists = False
                for row in rows:
                    for widget in row:
                        wid = widget['widget_id']
                        if wid == field[0]:
                            exists = True
                            break

                if not exists:
                    layout_def['rows'] += [[{'ncols': 1, 'widget_id': field[0]}]]

        memberlayout.setLayoutDefinition(layout_def)

    def addWMAction(self):
        """ adds an action in user actions """
        redir = '${portal_url}/portal_webmail/webmailRedirect.html?user_id=${member}'
        cond = "member and portal.portal_webmail.canHaveMailBox()"
        action = {
                'id': 'webmail',
                'name': '_list_mail_',
                'action': 'string:%s' % redir,
                'condition': 'python: %s' % cond,
                'permission': 'View',
                'category': 'user',
                }

        self.deleteActions({'portal_actions': ['webmail',]})
        self.verifyAction('portal_actions', **action)

        redir = '${portal_url}/portal_webmail/configure.html'
        action = {
                'id': 'webmail_global',
                'name': 'cpsma_configure_mailtool',
                'action': 'string:%s' % redir,
                'condition': 'member',
                'permission': 'Manage MailTool',
                'category': 'global',
                }

        self.deleteActions({'portal_actions': ['webmail_global',]})
        self.verifyAction('portal_actions', **action)

        # we don't want to see notify_content in the webmail
        if CPSSubscriptions == 0:
            return

        # check CPSSubscriptions is installed
        stool = getToolByName(self.portal, 'portal_subscriptions', None)
        if stool is None:
          return

        ptypes = "('Portal', 'CPSMailAccess Message', 'CPSMailAccess Box', 'CPSMailAccess Folder')"
        condition = "object.portal_type not in %s" % ptypes

        action = {'id' : 'notify_content',
                  'name' : 'action_notify_content',
                  'action' : 'string:${object_url}/content_notify_email_form',
                  'condition' : 'python:%s' % condition,
                  'permission' :  (CanNotifyContent,),
                  'category' : 'object',
                  }
        self.deleteActions({'portal_subscriptions': ['notify_content',]})
        self.verifyAction('portal_subscriptions', **action)

    def setupPermissions(self):
        """ sets up permission """
        self.setupPortalPermissions(permissions, self.portal)

    def linkFiveActionTool(self):
        """ verify that five action tool is linked """
        five_actions = 'portal_fiveactions'
        if not hasattr(self.portal, five_actions):
            self.portal.manage_addProduct['CMFonFive'].\
                manage_addTool(type='Five Actions Tool')

        portal_actions = self.portal.portal_actions

        if five_actions not in portal_actions.listActionProviders():
            portal_actions.addActionProvider(five_actions)

    def setupPortlets(self):
        """ installing portlets """
        portlets = ({'identifier': 'webmail_navigation',
                     'type': 'Custom Portlet',
                     'slot': 'left',
                     'order': 0,
                     'render_method': 'portlets_treeview',
                     'Title': 'Webmail navigation',
                    },
                    {'identifier': 'webmail_files',
                     'type': 'Custom Portlet',
                     'slot': 'right',
                     'order': 0,
                     'render_method': 'portlets_attached_files',
                     'Title': 'Attached Files',
                    },
                    )

        self.verifyPortlets(portlets, self.portal.portal_webmail)

    def setupBoxesorPortlets(self):
        """ sets attached file and treeview boxes """
        if hasattr(self.portal, 'portal_cpsportlets'):
            self.setupPortlets()
        else:
            self.setupBoxes()

    def upgrade_parameters(self):
        # this is done, no matter wich version is currently run
        self.log('checking portal_webmail parameters')
        wm = self.portal.portal_webmail
        params = wm.default_connection_params
        global default_parameters

        for parameter in default_parameters:
            if not params.has_key(parameter):
                params[parameter] = default_parameters[parameter]

        for id, box in wm.objectItems():
            if not isinstance(box, MailBox):
                continue

            if not hasattr(box, '_connection_params'):
                setattr(box, '_connection_params', {})

            for item in params.keys():
                if not box._connection_params.has_key(item):
                    box._connection_params[item] = params[item]


    def upgrade(self, new_version=None, old_version=None, force=False):
        """ upgrades an existing version of CPSMailAccess

            if old_version is set to None,
            the upgrader will upgrade from the first existing version
            to the last one
        """
        if not hasattr(self.portal, 'portal_webmail'):
            self.install()
            return None

        old_version = self._shorcutName(old_version)
        new_version = self._shorcutName(new_version)

        self.upgrade_parameters()

        # creating a temporary directory for mail storage
        wm = self.portal.portal_webmail
        if not hasattr(wm, '_maildeliverer'):
            self.log('adding Mail deliverer')
            from Products.CPSMailAccess.smtpmailer import SmtpMailer
            temp_dir = os.path.dirname(os.tempnam())
            temp_dir = os.path.join(temp_dir, 'maildir')
            wm._maildeliverer = SmtpMailer(temp_dir, 1)

        if old_version is None and new_version is None:
            self.setupTranslations()
            self.finalize()
            return None

        if old_version is None:
            old_version = self._versions[0]
        if (old_version not in self._versions or
            new_version not in self._versions):
            raise Exception('unknown versions')

        if old_version == (1, 0, 0, 'b1') and  new_version == (1, 0, 0, 'b2'):
            self.upgrade_b1_to_b2(force)

        self.setupTranslations()
        self.finalize()

    def _shorcutName(self, name):
        if name in ('beta2', 'b2'):
            return (1, 0, 0, 'b2')
        elif name in ('beta1', 'b1'):
            return (1, 0, 0, 'b1')
        else:
            return name

    def upgrade_b1_to_b2(self, force=False):

        self.log('upgrading portal_webmail to beta 2')
        wm = self.portal.portal_webmail
        if (not hasattr(wm, '__version__') or wm.__version__ !=  (1, 0, 0, 'b2')
            or force):
            wm.__version__ = (1, 0, 0, 'b2')

            from Products.CPSMailAccess.smtpmailer import SmtpMailer
            # creating a temporary directory for mail storage
            temp_dir = os.path.dirname(os.tempnam())
            temp_dir = os.path.join(temp_dir, 'maildir')
            wm._maildeliverer = SmtpMailer(temp_dir, 1)

        self.log('upgrading boxes to beta 2')
        from BTrees.OOBTree import OOBTree

        for id, box in wm.objectItems():
            if not isinstance(box, MailBox):
                continue
            self.log('checking box: %s' % id)
            if (not hasattr(box, '__version__') or
                box.__version__ != (1, 0, 0, 'b2') or force):
                # beta 1, upgrading to beta 2
                self.log('upgrading box %s to beta 2' % id)
                box.__version__ = (1, 0, 0, 'b2')

            zcat = box._getZemanticCatalog()
            if not hasattr(zcat, '_message_ids'):
                self.log('    old catalog, upgrading')
                zcat._message_ids = OOBTree()

def install(self):
    """Installation is done here.

    Called by an external method for instance.
    """
    installer = CPSMailAccessInstaller(self)
    installer.upgrade()
    return installer.logResult()

def upgrade(self, new_version=None, old_version=None, force=False):
    """ upgrades """
    installer = CPSMailAccessInstaller(self)
    installer.upgrade(new_version, old_version, force)
    return installer.logResult()

def upgrade_to_beta2(self):
    return upgrade('b2')

def force_to_beta2(context=None):
    return upgrade('b2', force=True)
