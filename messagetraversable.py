# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
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
from zLOG import LOG, INFO, DEBUG

from zope.interface import implements
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.interfaces import IMessageTraverser, IMailMessage
from Products.Five.traversable import FiveTraversable
from zope.component import getView, ComponentLookupError
#from zope.app.pagetemplate.simpleviewclass import SimpleViewClass

class MessageTraversable(FiveTraversable):
    """ the main container
    >>> f = MessageTraversable(None)
    >>> IMessageTraverser.providedBy(f)
    True
    """
    implements(IMessageTraverser)

    def __init__(self, subject):
        FiveTraversable.__init__(self, subject)

    def traverse(self, path='', request=None):

        context = self._subject
        # let's scan parts
        if IMailMessage.providedBy(context):
            # first of all let's try to find a view out of the path name
            # next let's try to find the part in non persistent
            # section
            if type(path) is list and len(path) == 1:
                cpath  = path[0]
            else:
                cpath = path

            if context._v_volatile_parts.has_key(cpath):
                part = context._v_volatile_parts[cpath]
            # next let's look in persistent parts
            elif hasattr(context, cpath):
                part = getattr(context, cpath)
            # todo : generate the part on the fly and loads it
            # in  context._v_volatile_parts
            else :
                # TODO on the fly generation here later
                # if founded, otherwise has to raise something
                # for now this is generatnig an emptymessage
                part = MailMessage(cpath)
                context._v_volatile_parts[cpath] = part

            if part is not None:
                return part
            else:
                return FiveTraversable.traverse(self, path, '')
        else:
            return FiveTraversable.traverse(self, path, '')

