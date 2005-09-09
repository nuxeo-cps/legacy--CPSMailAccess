#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
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

"""
 ConnectionList is a thread-safe list of all active connections
 inactive connections are killed
"""
from zLOG import LOG, INFO, DEBUG

import time
import os, sys
import thread

from UserList import UserList

from zope.interface import implements

from Products.CPSMailAccess.interfaces import IConnectionList
from Products.CPSMailAccess.connectionwatcher import ConnectionWatcher


class ConnectionList(UserList):
    """ this is a list with a thread
        wich keep connection alive
        or kills them
        and also maintain idle times

    >>> f = ConnectionList()
    >>> IConnectionList.providedBy(f)
    True
    """
    implements(IConnectionList)

    connection_guard = None
    connection_generators = {}
    lock = thread.allocate_lock()

    def __init__(self, initlist=None):
        UserList.__init__(self, initlist)
        # instanciates a connection keeper
        self.connection_guard = ConnectionWatcher(self)
        self.connection_guard.start()

    """
    def __del__(self):
        "" when the list is removed, we need to check
        if a thread is running, to stop it
        ""
        if self.connection_guard.isAlive():
            self.connection_guard.stop()

        for base in self.__class__.__bases__:
            # Avoid problems with diamond inheritance.
            basekey = 'del_' + str(base)
            if not hasattr(self, basekey):
                setattr(self, basekey, 1)
            else:
                continue
            # Call this base class' destructor if it has one.
            if hasattr(base, "__del__"):
                base.__del__(self)
    """
    def listConnectionTypes(self):
        types = []
        self.lock.acquire()
        try:
            for generator_key in self.connection_generators.keys():
                types.append(generator_key)
        finally:
            self.lock.release()
        return types

    def registerConnectionType(self, connection_type, method):
        self.lock.acquire()
        try:
            self.connection_generators[connection_type] = method
        finally:
            self.lock.release()

    def _getConnectionObject(self, connection_params, connection_number=0):
        """ _getConnectionObject """
        # XXXX no lock here beware of the deadlock
        connection_type = connection_params['connection_type']
        if self.connection_generators.has_key(connection_type):
            meth = self.connection_generators[connection_type]
            new_connection = meth(connection_params)
            # XXXX auto-login
            if new_connection.getState() != 'AUTH':
                new_connection.login(connection_params['login'],
                    connection_params['password'])
            new_connection.connection_number = connection_number
            return new_connection
        else:
            raise ValueError("no connector for %s" % connection_type)

    def getConnection(self, connection_params, connection_number=0):
        """ return connection object """
        result = None
        self.lock.acquire()
        try:
            uid = connection_params['uid']
            connection_type = connection_params['connection_type']
            for connection in self:
                if (connection.uid == uid and
                    connection.connection_type == connection_type and
                    connection.connection_number == connection_number):
                    result = connection
                    break
            if not result:
                newob = self._getConnectionObject(connection_params,
                                                  connection_number)
                result = newob
                self.append(newob)
        finally:
            self.lock.release()
        return result

    def killConnection(self, uid, connection_type, connection_number=0):
        """ see interface
        """
        self.lock.acquire()
        try:
            for connection in self:
                if (connection.uid == uid and
                    connection.connection_type == connection_type and
                    connection.connection_number == connection_number):
                    self.remove(connection)
                    connection.logout()
                    #connection.close()
                    del connection

        finally:
            self.lock.release()

    def killAllConnections(self):
        """ see interface
        """
        self.lock.acquire()
        try:
            for connection in self:
                self.remove(connection)
                connection.logout()
                #connection.close()
                del connection
        finally:
            self.lock.release()



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
                if qualifyModule(item+'.py'):
                    ul = getattr(u, item)

                    if hasattr(ul, 'makeMailObject') and \
                        hasattr(ul, 'connection_type') :
                        connection_list.registerConnectionType(ul.connection_type,
                            ul.makeMailObject)

