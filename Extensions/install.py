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
        self.setupDefaultAddressBooks()
        self.setupDefaultMailingListsDirectory()
        self.setupMembersSchemasAndLayouts()
        self.addWMAction()
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
                'search_substring_fields': ['fullname', 'email'],
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
                'search_substring_fields': ['fullname', 'email'],
                'directory_ids': [],
                'directory_type': 'CPS ZODB Directory',
                },
            }

        privaddressbooklinks_directory = {
            'type': 'CPS Local Directory',
            'data': {
                'title': 'label_personal_addressbooklinks',
                'schema': 'addressbook',
                'schema_search': 'addressbook_search',
                'layout': 'addressbook_links',
                'layout_search': 'addressbook_search',
                'acl_directory_view_roles': 'Manager; Member',
                'acl_entry_create_roles': 'Manager; Member',
                'acl_entry_delete_roles': 'Manager; Member',
                'acl_entry_view_roles': 'Manager; Member',
                'acl_entry_edit_roles': 'Manager; Member',
                'id_field': 'id',
                'title_field': 'fullname',
                'search_substring_fields': ['id'],
                'directory_ids': ['addressbook', 'members'],
                'directory_type': 'CPS Indirect Directory',
                },
            }

        directories = {
            'addressbook': addressbook_directory,
            '.addressbook': privaddressbook_directory,
            '.addressbook_links': privaddressbooklinks_directory,
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
                    'read_process_expr': """python:(str(givenName) + " " \
                        + str(sn)).strip() or id""",
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
                    'type': 'User Identifier Widget',
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


        addressbook_links_layout = {
            'widgets': {
                'id': {
                    'type': 'Directory Entry Widget',
                    'data': {
                        'fields': ('id',),
                        'is_required': 1,
                        'label': 'label_user_name',
                        'label_edit': 'label_user_name',
                        'is_i18n': 1,
                        'readonly_layout_modes': ('edit',),
                        'vocabulary': 'addressbook_links',
                        'directory': '.addressbook_links',
                        'entry_type': 'id',
                        'skin_name': 'cpsdirectory_entry_view',
                        'popup_mode': 'search',
                        },
                    },
                'givenName': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('givenName',),
                        'label': 'label_first_name',
                        'label_edit': 'label_first_name',
                        'is_i18n': 1,
                        'hidden_layout_modes': ('create', 'edit'),
                        'display_width': 20,
                        'size_max': 0,
                    },
                },
                'sn': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('sn',),
                        'label': 'label_last_name',
                        'label_edit': 'label_last_name',
                        'is_i18n': 1,
                        'hidden_layout_modes': ('create', 'edit'),
                        'display_width': 20,
                        'size_max': 0,
                    },
                },
                'fullname': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('fullname',),
                        'label': 'label_full_name',
                        'label_edit': 'label_full_name',
                        'is_i18n': 1,
                        'hidden_layout_modes': ('create', 'edit', 'search'),
                        'display_width': 30,
                        'size_max': 0,
                    },
                },
                'email': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('email',),
                        'label': 'label_email',
                        'label_edit': 'label_email',
                        'is_i18n': 1,
                        'hidden_layout_modes': ('create', 'edit'),
                        'display_width': 30,
                        'size_max': 0,
                    },
                },
            },
            'layout': {
                'style_prefix': 'layout_dir_',
                'flexible_widgets': (),
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

        layouts = {
            'addressbook': addressbook_layout,
            'addressbook_search': addressbook_search_layout,
            'addressbook_links': addressbook_links_layout,
            }
        self.verifyLayouts(layouts)

        self.log("Schemas and layouts related to address book directories added")

        self.log("Setting up vocabulary needed in the id widget, in the addressbook_links layout")
        addressbook_links_vocabulary = {
            'type': 'CPS Indirect Directory Vocabulary',
            'data': {
                'directory': '.addressbook_links',
                },
            }
        vocabulary = {
            'addressbook_links': addressbook_links_vocabulary,
            }
        self.verifyVocabularies(vocabulary)
        self.log("Vocabulary addressbook added")

    def setupDefaultMailingListsDirectory(self):
        """ sets up mailing list directory
        """

        self.log("Setting up default mailing lists directory")

        # removing 'mailinglists' directory, which is the old name for
        # directory '.mailinglists'. Old personal instances in users' home
        # folders will have to be deleted manually
        dirtool = self.portal.portal_directories
        if 'mailinglists' in dirtool.objectIds():
            dirtool.manage_delObjects(['mailinglists'])
            self.log("Removing old directory 'mailinglists' from portal_directory ; old instances in users'home folders will have to be deleted manually")

        mailinglists_directory = {
            'type': 'CPS Local Directory',
            'data': {
                'title': 'label_mailinglists_directory',
                'schema': 'mailinglists',
                'schema_search': 'mailinglists',
                'layout': 'mailinglists',
                'layout_search': 'mailinglists_search',
                'acl_directory_view_roles': 'Manager; Member',
                'acl_entry_create_roles': 'Manager; Member',
                'acl_entry_delete_roles': 'Manager; Member',
                'acl_entry_view_roles': 'Manager; Member',
                'acl_entry_edit_roles': 'Manager; Member',
                'id_field': 'id',
                'title_field': 'id',
                'search_substring_fields': ['id', 'emails'],
                'directory_ids': [],
                'directory_type': 'CPS ZODB Directory',
                },
            }

        directories = {
            '.mailinglists': mailinglists_directory,
            }

        self.verifyDirectories(directories)

        self.log("Mailing lists directory added")

        portal = self.portal

        mailinglists_schema = {
            'id': {
                'type': 'CPS String Field',
                'data': {
                    'default_expr': 'string:',
                    },
                },
            'emails': {
                'type': 'CPS String List Field',
                'data': {
                    'default_expr': 'python:[]',
                    },
                },
            }

        schemas = {
            'mailinglists': mailinglists_schema,
            }
        self.verifySchemas(schemas)

        mailinglists_layout = {
            'widgets': {
                'emails': {
                    'type': 'Unordered List Widget',
                    'data': {
                        'fields': ('emails',),
                        'is_required': 0,
                        'label': 'label_emails',
                        'label_edit': 'label_emails',
                        'help': 'label_emails_help',
                        'is_i18n': 1,
                        'width': 40,
                        'height': 5,
                        },
                    },
                'id': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('id',),
                        'is_required': 1,
                        'label': 'label_mailinglist_name',
                        'label_edit': 'label_mailinglist_name',
                        'is_i18n': 1,
                        'display_width': 20,
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
                    [{'ncols': 2, 'widget_id': 'emails'},
                     ],
                    ],
                },
            }

        mailinglists_search_layout = {
            'widgets': {
                'emails': {
                    'type': 'Unordered List Widget',
                    'data': {
                        'fields': ('emails',),
                        'is_required': 0,
                        'label': 'label_emails',
                        'label_edit': 'label_emails',
                        'is_i18n': 1,
                        'width': 40,
                        'height': 5,
                        },
                    },
                'id': {
                    'type': 'String Widget',
                    'data': {
                        'fields': ('id',),
                        'is_required': 0,
                        'label': 'label_mailinglist_name',
                        'label_edit': 'label_mailinglist_name',
                        'is_i18n': 1,
                        'display_width': 20,
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
                    [{'ncols': 2, 'widget_id': 'emails'},
                     ],
                    ],
                },
            }

        layouts = {
            'mailinglists': mailinglists_layout,
            'mailinglists_search': mailinglists_search_layout,
            }
        self.verifyLayouts(layouts)

        self.log("Schemas and layouts related to mailing lists directory added")

    def setupMembersSchemasAndLayouts(self):
        """ adds a checkbox that tells if the user
            has webmail capabilities
        """

        self.log(" Setting up schemas and layouts")
        portal = self.portal
        stool = portal.portal_schemas
        memberschema = stool.members
        fields = memberschema.objectIds()
        pmd = portal.portal_memberdata

        if not 'f__webmail_enabled' in fields:
            memberschema.addField('webmail_enabled', 'CPS Int Field',
                                    acl_write_roles_str='Manager, Owner')
        if not pmd.hasProperty('webmail_enabled'):
            pmd.manage_addProperty('webmail_enabled', '', 'boolean')

        ltool = portal.portal_layouts
        memberlayout = ltool.members
        widgets = memberlayout.objectIds()
        layout_def = memberlayout.getLayoutDefinition()
        if not 'w__webmail_enabled' in widgets:
            memberlayout.addWidget('webmail_enabled', 'Boolean Widget',
                                   fields='webmail_enabled',
                                   label='label_iwebmail_enabled',
                                   label_edit='label_webmail_enabled',
                                   is_i18n=1,
                                   )
            layout_def['rows'] += [[{'ncols': 1, 'widget_id': 'webmail_enabled'}]]

        memberlayout.setLayoutDefinition(layout_def)

    def addWMAction(self):
        """ adds an action in user actions
        """
        action = {
                'id': 'webmail',
                'name': '_list_mail_',
                'action':
         'string:${portal_url}/portal_webmail/webmail_redirect?user_id=${member}',
                'condition': 'member',
                'permission': 'View',
                'category': 'user',
                }
        self.verifyAction('portal_actions', **action)

def install(self):
    """Installation is done here.

    Called by an external method for instance.
    """
    installer = CPSMailAccessInstaller(self)
    installer.install()
    return installer.logResult()
