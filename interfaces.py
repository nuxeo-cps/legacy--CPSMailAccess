# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
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

from zope.interface import Interface
from zope.app.container.interfaces import IContained, IContainer
from zope.app.container.constraints import ContainerTypesConstraint
from zope.schema import Field

class ICPSMessage(Interface):
    """ A Mail message container.
    
        ICPSMessage stores the content of a message
        this content can be composed of headers,
        ID, and optionnaly the body      
    """
    pass
    
class ICSPMailFolder(IContainer):
    """ A Message container
        it can contains also Mail Folders
    """    
    def getMessageList(recursive=False):
        """ Retrieves all contained messages with recursive option            
        """
    
    
class ICSPMailFolderContained(IContained):
    """Objects that contain Message should implement this interface."""
    __parent__ = Field(
        constraint = ContainerTypesConstraint(ICSPMailFolder)) 
          