#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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
from UserList import UserList
from zope.interface import implements
import os, sys
from Products.CPSMailAccess.interfaces import IConnectionList
from Products.CPSMailAccess.connectionwatcher import ConnectionWatcher

class ConnectionList(UserList):
    """ this is a list with a thread
        wich keep connection alive
        or kills them
        and also maintain idle times
    """
    implements(IConnectionList)

    connection_guard = None
    connection_generators = {}

    def __init__(self, initlist=None):
        UserList.__init__(self, initlist)
        # instanciates a connection keeper
        self.connection_guard = ConnectionWatcher(self)
        self.connection_guard.start()

    def getCurrentId(self):
        #### to be done
        return 'tarek'

    def listConnectionTypes(self):
        types = []
        for generator_key in self.connection_generators.keys():
            types.append(generator_key)
        return types

    def registerConnectionType(self, connection_type, method):
        self.connection_generators[connection_type] = method


    #def killThread(self):
    #    if self.connection_guard:
    #        self.connection_guard.stop()


    def _getConnectionObject(self, connection_params):

        connection_type = connection_params['connection_type']
        if self.connection_generators.has_key(connection_type):
            meth = self.connection_generators[connection_type]
            new_connection = meth(connection_params)
            return new_connection
        else:
            raise ValueError("no connector for %s" % connection_type)

    def getConnection(self, connection_params):
        result = None
        for connection in self:

            uid = self.getCurrentId()
            connection_type = connection_params['connection_type']

            if (connection.uid == uid) and \
                (connection.connection_type == connection_type):
                result = connection
                break

        if not result:
            newob = self._getConnectionObject(connection_params)
            result = newob
            self.append(newob)

        return result

""" this method gives
    a list of Product folder
    connection classes
"""
landmark = 'Products.CPSMailAccess'

def qualifyModule(module_name):
    return module_name.endswith('connection.py') and \
       len(module_name)>len('connection.py') and \
       module_name <> 'baseconnection.py'

def registerConnections(connection_list):
    m = sys.modules[landmark]
    path = m.__path__[0]
    units = os.listdir(path)

    for unit in units:
        if qualifyModule(unit):
            # XXXXX linux specific
            # see how to make it multi os
            unit = unit[:-3]
            u = __import__(landmark+'.'+unit)
            current = u.CPSMailAccess
            u = current
            for item in dir(u):
                if qualifyModule(unit):
                    ul = getattr(u, item)
                    if hasattr(ul, 'makeMailObject') and \
                        hasattr(ul, 'connection_type') :
                        connection_list.registerConnectionType(ul.connection_type,
                            ul.makeMailObject)
