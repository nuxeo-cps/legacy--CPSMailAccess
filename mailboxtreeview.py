# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
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
""" MailBoxTreeView
    A MailBoxTreeView shows a treeview
    from the mail box
"""
# XX see for dependencies
from Products.CPSBoxes.BaseBox import BaseBox
try:
    from Products.CMFCore.permissions import View, ModifyPortalContent
except ImportError:
    # BBB for CMF 1.4, remove this in CPS 3.4.0
    from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent

from Globals import InitializeClass

factory_type_information = (
    {'id': 'MailBoxTreeView',
     'title': 'portal_type_MailBoxTreeView_title',
     'description': 'portal_type_MailBoxTreeView_description',
     'meta_type': 'MailBoxTreeView',
     'icon': 'box.png',
     'product': 'CPSMailAccess',
     'factory': 'manage_addMailBoxTreeview',
     'immediate_view': 'basebox_edit_form',
     'filter_content_types': 0,
     'actions': ({'id': 'view',
                  'name': 'View',
                  'action': 'mailboxtreeview_view',
                  'permissions': (View,)},
                 {'id': 'edit',
                  'name': 'Edit',
                  'action': 'basebox_edit_form',
                  'permissions': (ModifyPortalContent,)},
                 ),
     # additionnal cps stuff
     'cps_is_portalbox': 1,
     },
    )

class MailBoxTreeView(BaseBox):
    meta_type = 'MailBoxTreeView'
    portal_type = meta_type


InitializeClass(MailBoxTreeView)

def manage_addMailBoxTreeview(dispatcher, id, REQUEST=None, **kw):
    """Add a MailBoxTreeView Box."""
    ob = MailBoxTreeView(id, **kw)
    dispatcher._setObject(id, ob)
    ob = getattr(dispatcher, id)
    ob.manage_permission(View, ('Anonymous',), 1)
    if REQUEST is not None:
        url = dispatcher.DestinationURL()
        REQUEST.RESPONSE.redirect('%s/manage_main' % url)

