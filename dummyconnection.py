# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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

    def login(self, user, password):

        self.connected = True
        return True

    def logout(self):
        self.connected = False
        return True

    def noop(self):
        pass

connection_type = 'DUMMY'

def makeMailObject(connection_params):

    try:
        newob =  DummyConnection(connection_params)
    except IMAP4.abort:
        # we probablyhave a socket error here
        raise ConnectionError("socket error")
    else:
        newob.login(uid, password)
        print str('created '+str(newob))
        return newob
