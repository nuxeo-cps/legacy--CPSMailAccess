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

import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
import os
from Products.CPSMailAccess.connectionwatcher import ConnectionWatcher
from Products.CPSMailAccess.connectionlist import ConnectionList
from Products.CPSMailAccess.dummyconnection import DummyConnection
from Products.CPSMailAccess.interfaces import IConnectionWatcher
from time import time,sleep

installProduct('Five')

class ConnectionWatcherTestCase(ZopeTestCase):

    def test_simpleInstance(self):
        # testing instanciation
        watcher = ConnectionWatcher()
        self.assertNotEquals(watcher, None)

    def test_threadStopStart(self):
        # testing stops and starts
        watcher = ConnectionWatcher()
        watcher.start()
        self.assertEquals(watcher.running, 1)
        watcher.stop()
        self.assertEquals(watcher.running, 0)

    def test_ListWatching(self):
        # checking that silent connection get removed
        my_list = ConnectionList()
        my_list.connection_guard.sleep_time = 0.1
        my_list.connection_guard.idle_time = 0.1

        connection_params = {'uid' : 'admin', 'connection_type' : 'DUMMY'}

        new_connection = DummyConnection(connection_params)
        new_connection.login('admin','admin')
        my_list.append(new_connection)

        self.assertEquals(len(my_list), 1)
        sleep(3)
        self.assertEquals(my_list, [])

    def test_register_threads(self):

        class FakeThread:
            def stop(self):
                pass

        fake_1 = FakeThread()
        fake_2 = FakeThread()

        from Products.CPSMailAccess import connectionwatcher
        connectionwatcher.cleanThreads()

        self.assertEquals(connectionwatcher.thread_instances, [])
        connectionwatcher.registerThreadInstance(fake_1)
        connectionwatcher.registerThreadInstance(fake_2)

        self.assertEquals(len(connectionwatcher.thread_instances), 2)
        connectionwatcher.cleanThreads()
        self.assertEquals(connectionwatcher.thread_instances, [])

    def test_Interface(self):
        # make sure the contract is respected
        from zope.interface.verify import verifyClass
        self.failUnless(verifyClass(IConnectionWatcher, ConnectionWatcher))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ConnectionWatcherTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.connectionwatcher'),
        ))
