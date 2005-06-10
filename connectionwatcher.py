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
from zope.schema.fieldproperty import FieldProperty
from zope.interface import implements
from interfaces import IConnectionWatcher
from threading import Thread
from time import sleep
import atexit
from Products.CPSMailAccess.interfaces import IConnectionWatcher

class ConnectionWatcher(Thread):
    """ ConnectionWatcher
    >>> f = ConnectionWatcher()
    >>> IConnectionWatcher.providedBy(f)
    True
    """
    implements(IConnectionWatcher)

    parent = None

    sleep_time = FieldProperty(IConnectionWatcher['sleep_time'])
    idle_time = FieldProperty(IConnectionWatcher['idle_time'])

    terminated = False

    def __init__(self, parent=None, sleep_time=2, idle_time=60):
        Thread.__init__(self)
        self.parent = parent
        self.sleep_time = sleep_time
        self.idle_time = idle_time
        self.running = 1
        self.setDaemon(True)
        registerThreadInstance(self)

    def stop(self):
        """ see interface
        >>> f = ConnectionWatcher()
        >>> f.start()
        >>> f.stop()
        >>> f.running
        0
        """
        if self.running:
            self.running = 0
            self.join()

    def run(self):
        """ see interface
        >>> f = ConnectionWatcher()
        >>> f.start()
        >>> f.running
        1
        """
        while self.running:
            if self.parent:
                connection_list = self.parent
                for connection in connection_list:
                    connection.idle_time += self.sleep_time
                    # connection is sleeping for too long
                    # closing and cleaning it
                    if connection.idle_time >= self.idle_time:
                        uid = connection.uid
                        type_ = connection.connection_type
                        connection_list.killConnection(uid, type_)

            sleep(self.sleep_time)

# thread cleaning
thread_instances = []

def registerThreadInstance(thread_instance):
    if thread_instances.index < 0:
        thread_instances.append(thread_instance)

def cleanThreads():
    if thread_instances:
        for thread_instance in thread_instances:
            if hasattr(thread_instance, 'stop'):
                thread_instance.stop()


atexit.register(cleanThreads)
