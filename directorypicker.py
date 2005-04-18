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

"""DirectoryPicker

   An adapter to CPS Directories
   it encaspulates it to proved a simpler API
   for migrations
"""

from zope.interface import implements
from Products.Five import BrowserView
from interfaces import IDirectoryPicker
from utils import getToolByName

class DirectoryPicker(object):
    """ the main container

    >>> f = DirectoryPicker(None)
    >>> IDirectoryPicker.providedBy(f)
    True
    """
    implements(IDirectoryPicker)

    def __init__(self, portal_directory):
        self.context = portal_directory

    def getDirectoryList(self):
        """ see interface """

        return self.context.listVisibleDirectories()

    def searchEntries(self, directory_name, return_fields=None, **kw):
        """ see interface """

        dir_ = self.context[directory_name]
        return dir_.searchEntries(return_fields, **kw)


class DirectoryPickerView(BrowserView):

    def getEntries(self):
        """ returns entries """
        entries = self.context.getMailDirectoryEntries()
        return entries

    def searchUsers(self, email):
        """ search adressbooks and renders results """
        if email.strip() == '':
            return []
        return self.context.searchDirectoryEntries(email)

    def getEditorContainers(self):
        """ gets the editor containers """
        mbox = self.context
        msg = mbox.getCurrentEditorMessage()
        Tos = msg.getHeader('To')
        Ccs = msg.getHeader('Cc')
        Bccs = msg.getHeader('BCc')
        return {'To': Tos, 'Cc' : Ccs, 'BCc' : Bccs}
