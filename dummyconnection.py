# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziad� <tz@nuxeo.com>
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
from zope.interface import implements
from interfaces import IConnection
from Products.CPSMailAccess.baseconnection import BaseConnection

class DummyConnection(BaseConnection):
    """ Dummy connection
    >>> f = DummyConnection()
    >>> IConnection.providedBy(f)
    True
    """
    implements(IConnection)

    def __init__(self, connection_params={}):

        connection_params['HOST'] = 'the seventh floor'
        BaseConnection.__init__(self, connection_params)

    def login(self, user, password):
        self.state = 'AUTH'
        return True

    def logout(self):
        self.state = 'NOAUTH'
        return True

    def getState(self):
        return self.state

    def noop(self):
        pass

    def list(self):
        return []

connection_type = 'DUMMY'

def makeMailObject(connection_params):
    newob =  DummyConnection(connection_params)
    uid = connection_params['uid']
    newob.login(uid, 'password')
    #print str('created '+str(newob))
    return newob
