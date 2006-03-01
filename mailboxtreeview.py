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
from Globals import InitializeClass, DTMLFile
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base

from OFS.PropertyManager import PropertyManager

from Products.CMFCore.utils import _verifyActionPermissions
from Products.CMFCore.permissions import View, ModifyPortalContent,\
                                                ManagePortal
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.utils import getToolByName

from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from zLOG import LOG, DEBUG
from Products.DCWorkflow.Guard import Guard

## monkey patch to add properties in portal_types

from AccessControl.PermissionRole import PermissionRole
from Products.CMFCore.TypesTool import TypeInformation
from Products.CMFCore.TypesTool import FactoryTypeInformation as FTI
from Products.CMFCore.permissions import ManageProperties

TypeInformation.manage_propertiesForm = PropertyManager.manage_propertiesForm
TypeInformation.manage_addProperty__roles__ = PermissionRole(ManageProperties)
TypeInformation.manage_delProperties__roles__ = PermissionRole(ManageProperties)

ftiprops_ids = [p['id'] for p in FTI._properties]

if 'cps_is_portalbox' not in ftiprops_ids:
    FTI._properties = FTI._properties + (
        {'id':'cps_is_portalbox', 'type': 'boolean', 'mode':'w',
         'label':'CPS Portal Box'},
        )
    FTI.cps_is_portalbox = 0
## end of monkey patch

try:
    from Products.CMFCore.permissions import View, ModifyPortalContent
except ImportError:
    # BBB for CMF 1.4, remove this in CPS 3.4.0
    from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent

def createExpressionContext(sm, box, context):
    """Create a name space for TALES expressions.

    @param sm: SecurityManager instance
    @param box: Box instance
    @param context: Zope context (which object is being published)
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    data = {
        'box': box,
        'here': context,
        'portal': portal,
        'request': getattr(context, 'REQUEST', None),
        'user': sm.getUser(),
        'nothing': None,
        }
    return getEngine().getContext(data)

class BoxGuard(Guard):
    """DCWorkflow Guard with a box-specific name space.
    """
    def check(self, sm, box, context):
        """Checks conditions in this guard.

        @param sm: SecurityManager instance
        @param box: Box instance
        @param context: Zope context (which object is being published)
        """
        pp = self.permissions
        if pp:
            found = 0
            for p in pp:
                if sm.checkPermission(p, box):
                    found = 1
                    break
            if not found:
                return 0
        roles = self.roles
        if roles:
            # Require at least one of the given roles.
            found = 0
            u_roles = sm.getUser().getRolesInContext(box)
            for role in roles:
                if role in u_roles:
                    found = 1
                    break
            if not found:
                return 0
        expr = self.expr
        if expr is not None:
            econtext = createExpressionContext(sm, box, context)
            res = expr(econtext)
            if not res:
                return 0
        return 1

InitializeClass(BoxGuard)


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

class MailBoxTreeView(PortalContent, DefaultDublinCoreImpl, PropertyManager):

    isPortalBox = 1
    meta_type = 'MailBoxTreeView'
    portal_type = meta_type

    manage_options = (PropertyManager.manage_options +
                      ({'label': 'Guard', 'action': 'manage_guardForm'},) +
                      PortalContent.manage_options[:1] +
                      PortalContent.manage_options[3:] +
                      ({'label': 'Export', 'action': 'manage_export'},)
                     )

    security = ClassSecurityInfo()
    guard = None

    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w', 'label': 'Title'},

        {'id': 'provider', 'type': 'string', 'mode': 'w', 'label': 'Provider'},
        {'id': 'btype', 'type': 'string', 'mode': 'w', 'label': 'type of box'},

        {'id': 'box_skin', 'type': 'string', 'mode': 'w',
         'label': 'skin of the box'},
        {'id': 'minimized', 'type': 'boolean', 'mode': 'w',
         'label': 'Minimized'},
        {'id': 'closed', 'type': 'boolean', 'mode': 'w', 'label': 'Closed'},
        {'id': 'slot', 'type': 'string', 'mode': 'w', 'label': 'Slot'},
        {'id': 'order', 'type': 'int', 'mode': 'w', 'label': 'Order'},
        {'id': 'display_in_subfolder', 'type': 'boolean', 'mode': 'w',
         'label': 'Display in sub folder'},
        {'id': 'display_only_in_subfolder', 'type': 'boolean', 'mode': 'w',
         'label': 'Display only in sub folder'},
        {'id': 'locked', 'type': 'boolean', 'mode': 'w',
         'label': 'Locked box'},
    )

    def __init__(self, id, title='', category='basebox',
                 box_skin='here/box_lib/macros/mmcbox',
                 minimized=0, closed=0,
                 provider='nuxeo', btype='default', slot='creation_slot',
                 order=0,
                 display_in_subfolder=1,
                 display_only_in_subfolder=0, locked=0, **kw):
        DefaultDublinCoreImpl.__init__(self)
        self.id = id
        self.title = title
        self.category = category
        self.provider = provider
        self.box_skin = box_skin
        self.btype = btype
        self.slot = slot
        self.order = int(order)
        self.minimized = minimized
        self.closed = closed

        self.display_in_subfolder = display_in_subfolder
        self.display_only_in_subfolder = display_only_in_subfolder
        self.locked = locked


    #
    # ZMI
    #
    security.declareProtected(ManagePortal, 'manage_export')
    manage_export = DTMLFile('zmi/box_export', globals())

    security.declareProtected(ManagePortal, 'manage_guardForm')
    manage_guardForm = DTMLFile('zmi/manage_guardForm', globals())

    security.declareProtected(ModifyPortalContent, 'setGuardProperties')
    def setGuardProperties(self, props={}, REQUEST=None):
        """Postprocess guard values."""
        if REQUEST is not None:
            # XXX Using REQUEST itself should work.
            # but update is complaining it is not a dictionary
            props.update(REQUEST.form)

        # XXX found we must create a new instance every time.
        # not that much resource friendly...
        self.guard = BoxGuard()
        self.guard.changeFromProperties(props)

        if REQUEST is not None:
            return self.manage_guardForm(REQUEST,
                management_view='Guard',
                manage_tabs_message='Guard setting changed.')

    #
    # Public API
    #
    security.declarePublic('getSettings')
    def getSettings(self):
        """Return a dictionary of properties that can be overriden"""
        return {'slot': self.slot,
                'provider': self.provider,
                'btype': self.btype,
                'order': self.order,
                'minimized': self.minimized,
                'closed': self.closed,
                'box_skin': self.box_skin,
                }

    security.declareProtected('Manage Boxes', 'edit')
    def edit(self, **kw):
        """
        Default edit method, changes the properties.
        """
        self.manage_changeProperties(**kw)

    #
    # Internal API's mainly called from itself or other Zope tools
    #

    # XXX which security declaration?
    def getGuard(self):
        return self.guard

    def getTempGuard(self):
        """Used only by the time of using guard management form."""
        return BoxGuard().__of__(self)  # Create a temporary guard.

    security.declarePrivate('callAction')
    def callAction(self, actionid, **kw):
        """
        Call the given action.
        """
        ti = self.getTypeInfo()
        if ti is not None:
            actions = ti.getActions()
            for action in actions:
                if action.get('id', None) == actionid:
                    if _verifyActionPermissions(self, action):
                        meth = self.restrictedTraverse(action['action'])
                        if getattr(aq_base(meth), 'isDocTemp', 0):
                            return apply(meth, (self, self.REQUEST), kw)
                        else:
                            return apply(meth, (), kw)
        raise 'Not Found', (
            'Cannot find %s action for "%s"' %
            (actionid, self.absolute_url(relative=1)))

    security.declarePublic('getMacro')
    def getMacro(self, provider=None, btype=None):
        """
        GetMacros to render the box.
        """
        if not provider:
            provider = self.provider
        if not btype:
            btype = self.btype
        return 'here/boxes_%s/macros/%s_%s' % (provider, self.category, btype)

    security.declareProtected(View, 'edit_form')
    def edit_form(self, **kw):
        """
        Call the edit action.
        """
        return self.callAction('edit', **kw)

    def manage_afterAdd(self, item, container):
        if aq_base(self) is aq_base(item):
            # sets order attribute correctly
            order_max_set = 0
            order_max = -1
            my_slot = self.slot
            for box in container.objectValues():
                slot = getattr(aq_base(box), 'slot', None)
                if slot is not None and slot == my_slot:
                    order = getattr(aq_base(box), 'order', None)
                    if order is not None:
                        if order_max_set and order_max < order:
                            order_max = order
                        elif not order_max_set:
                            order_max_set = 1
                            order_max = order
            self.order = order_max + 1

        BaseBox.inheritedAttribute('manage_afterAdd')(self, item, container)

    def minimize(self, REQUEST=None):
        """Minimize the box using personal settings"""
        btool = getToolByName(self, 'portal_boxes')
        box_url = getToolByName(self, 'portal_url').getRelativeUrl(self)
        btool.updatePersonalBoxOverride(box_url,
                                     {'minimized':1, 'closed':0})
        if REQUEST is not None:
            goto = REQUEST.get('goto')
            if goto:
                REQUEST['RESPONSE'].redirect(goto)

    def maximize(self, REQUEST=None):
        """Maximize the box using personal settings"""
        btool = getToolByName(self, 'portal_boxes')
        box_url = getToolByName(self, 'portal_url').getRelativeUrl(self)
        btool.updatePersonalBoxOverride(box_url,
                                        {'minimized':0, 'closed':0})
        if REQUEST is not None:
            goto = REQUEST.get('goto')
            if goto:
                REQUEST['RESPONSE'].redirect(goto)

    def close(self, REQUEST=None):
        """Close the box using personal settings """
        btool = getToolByName(self, 'portal_boxes')
        box_url = getToolByName(self, 'portal_url').getRelativeUrl(self)
        btool.updatePersonalBoxOverride(box_url,
                                        {'closed':1})
        if REQUEST is not None:
            goto = REQUEST.get('goto')
            if goto:
                REQUEST['RESPONSE'].redirect(goto)

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

