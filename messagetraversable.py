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
from Products.CPSMailAccess.mailpart import MailPart
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

    def adaptPart(self, parent, part_name, raw_part):
        """ adapts part
        """
        adapter = MailPart(part_name, parent, raw_part)
        # XXX todo adapt cache level
        #adapter.cache_level = 2
        #adapter.loadMessage(raw_part.as_string())
        return adapter

    def fetchPart(self, message, part_num):
        """ creates a part load
        """
        return message.loadPart(part_num, part_content='', volatile=True)

    def traverse(self, path='', request=None):
        """ traverses the message
            XXXX traversed at this time by both
            part and message,
            might be splitted later in two classes
        """
        context = self._subject
        # let's scan parts
        if path !='':
            # first of all let's try to find a view out of the path name
            # next let's try to find the part in non persistent
            # section
            if type(path) is list and len(path) == 1:
                cpath  = path[0]
            else:
                cpath = path

            if IMailMessage.providedBy(context) and \
                context._v_volatile_parts.has_key(cpath):
                part = context._v_volatile_parts[cpath]

            # todo : generate the part on the fly and loads it
            # in  context._v_volatile_parts
            else:
                part = None
                # if the path is a number,
                # let's try to find it
                #if context.isMultipart():
                try:
                    # beware that in user side, parts starts at 1
                    path_num = int(cpath)-1
                except ValueError:
                    path_num = -1

                if path_num >= 0:
                    if context.isMultipart():
                        part_count = context.getPartCount()
                        # part are starting at 1
                        if path_num <= part_count:
                            # it's a persistent one
                            if path_num in context.getPersistentPartIds():
                                part = context.getPart(path_num)
                                if part is not None:
                                    # python raw msg, let's adapt it
                                    part = self.adaptPart(context, str(path_num), part)
                                else:
                                    # TODO we need to fetch it and add it in persistent
                                    raise NotImplementedError
                            # on the fly please
                            else:
                                # XXX TODO
                                part = self.fetchPart(context, path_num)
                                part = self.adaptPart(context, str(path_num), part)
                                context._v_volatile_parts[str(path_num)] = part
                else:
                    # let's try to find if it's a filename
                    index = 0
                    parts = context.getParts()
                    if parts is not None:
                        for element in parts:
                            if element.get_filename() == cpath:
                                part = self.adaptPart(context, str(index), element)
                            else:
                                index +=1
            if part is not None:
                return part

        # traversed all, this is a showable thing
        if type(path) is list:
            path = path[0]

        return FiveTraversable.traverse(self, path, '')

