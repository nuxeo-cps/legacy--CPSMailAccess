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

import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
import os
from Products.CPSMailAccess.connectionlist import ConnectionList
from Products.CPSMailAccess.connectionlist import registerConnections, qualifyModule
from Products.CPSMailAccess.dummyconnection import DummyConnection
from time import time,sleep

installProduct('FiveTest')
installProduct('Five')


class ConnectionListTestCase(ZopeTestCase):

    def test_ThreadDeaths(self):
        """ testing thread deaths
            this is a long test, might want to disable it
        """
        my_list = ConnectionList()

        my_list.connection_guard.sleep_time = 0.5
        my_list.connection_guard.idle_time = 0.1

        # thread will die in 0.1 second
        #print 'types'
        connection_params = {'uid' : 'admin', 'connection_type' : 'DUMMY'}

        self.assertEquals(my_list.listConnectionTypes(), [])

        for i in range(200):
            new_connection = DummyConnection(connection_params)
            new_connection.login('admin','admin')
            my_list.append(new_connection)

        # while there's still connection objects
        while len(my_list) > 0:
            sleep(0.1)
            #print('list count :'+str(len(my_list)))

    def test_qualifyModule(self):
        """ testing plugins scanner file finder
        """
        self.assertEquals(qualifyModule('imapconnection.py'), True)
        self.assertEquals(qualifyModule('baseconnection.py'), False)
        self.assertEquals(qualifyModule('connection.py'), False)

    def test_registerConnectionType(self):
        """ testing registery
        """
        from Products.CPSMailAccess import dummyconnection

        my_list = ConnectionList()
        my_list.registerConnectionType(dummyconnection.connection_type,
            dummyconnection.makeMailObject)

        self.assertEquals('DUMMY' in my_list.listConnectionTypes(), True)

        from Products.CPSMailAccess import imapconnection

        my_list = ConnectionList()
        my_list.registerConnectionType(imapconnection.connection_type,
            imapconnection.makeMailObject)

        self.assertEquals('IMAP' in my_list.listConnectionTypes(), True)

    def test_registerConnections(self):
        """ testing auto registery
        """
        my_list = ConnectionList()
        registerConnections(my_list)
        self.assertNotEquals(my_list.listConnectionTypes(), [])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ConnectionListTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.connectionlist'),
        doctest.DocTestSuite('Products.CPSMailAccess.dummyconnection'),
        ))