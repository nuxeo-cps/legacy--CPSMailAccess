# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziad� <tz@nuxeo.com>
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

    def adaptPart(self, part_name, raw_part):
        """ adapts part
        """
        adapter = MailMessage(part_name)
        # XXX todo adapt cache level
        adapter.cache_level = 2
        adapter.loadMessage(raw_part.as_string())
        return adapter

    def fetchPart(self, message, part_num):
        """ creates a part load
        """
        message.loadPart(part_num, volatile=True)
        return message._v_volatile_parts[str(part_num)]

    def traverse(self, path='', request=None):
        """ traverses the message
        """
        context = self._subject
        # let's scan parts
        if IMailMessage.providedBy(context) and (path !=''):
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
            else:
                part = None
                # if the path is a number,
                # let's try to find it
                if context.isMultipart():
                    try:
                        path_num = int(path)
                    except ValueError:
                        path_num = -1

                    if path_num >= 0:
                        part_count = context.getPartCount()
                        # part are starting at 1
                        if path_num <= part_count:
                            # it's a persistent one
                            if path_num in context.persistent_parts:
                              part = context.getPart(path_num-1)
                              if part is not None:
                                  # python raw msg, let's adapt it
                                  part = self.adaptPart(str(path_num), part)
                              else:
                                  # we need to fetch it
                                  raise 'TODO fetch needed  + add in persistent'
                            # on the fly please
                            else:
                                # XXX TODO
                                part = self.fetchPart(context, path_num)
                                part = self.adaptPart(str(path_num), part)
                                context._v_volatile_parts[str(path_num)] = part
                    else:
                        # let's try to find if it's a filename
                        index = 0
                        for element in context.getParts():
                            if element.get_filename() == path:
                                part = self.adaptPart(str(index), element)
                            else:
                                index +=1
            if part is not None:
                return part

        return FiveTraversable.traverse(self, path, '')

