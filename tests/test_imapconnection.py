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

import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
import os
from Products.CPSMailAccess.connectionlist import ConnectionList
from Products.CPSMailAccess.imapconnection import IMAPConnection
from time import time,sleep

installProduct('FiveTest')
installProduct('Five')

fake_imap_enabled = 1

"""
    xxxx
    need to finish fake IMAP lib
"""
class IMAPConnectionTestCase(ZopeTestCase):

    def makeConnection(self):
        my_params = {}
        my_params['HOST'] = 'localhost'
        my_params['UserID'] = 'tarek'
        my_params['UserPassword'] = 'tarek'
        my_params['TYPE'] = 'IMAP'
        myconnection = IMAPConnection(my_params)
        return myconnection

    def test_Instance(self):
        """ testing simple instanciation with parameters
        """
        if not fake_imap_enabled:
            return
        my_params = {}
        my_params['HOST'] = 'localhost'
        my_params['UserID'] = 'tarek'
        my_params['UserPassword'] = 'tarek'
        my_params['TYPE'] = 'IMAP'

        # regular connection
        myconnection = IMAPConnection(my_params)

        self.assertNotEqual(myconnection, None)

    def test_SSLInstance(self):
        """ testing simple SSL instanciation with parameters
        """
        if not fake_imap_enabled:
            return
        my_params = {}
        my_params['HOST'] = 'localhost'
        my_params['UserID'] = 'tarek'
        my_params['UserPassword'] = 'tarek'
        my_params['TYPE'] = 'IMAP'
        my_params['SSL'] = 1

        # regular connection
        myconnection = IMAPConnection(my_params)

        self.assertNotEqual(myconnection, None)

    def test_ConnectionParamsError(self):
        """ testing simple instanciation with missing parameters
        """
        from Products.CPSMailAccess.baseconnection import ConnectionParamsError
        my_params = {}

        self.failUnlessRaises(ConnectionParamsError, IMAPConnection, my_params)

    def test_login(self):
        """ testing simple instanciation with missing parameters
        """
        ob = self.makeConnection()

        login_result = ob.login('tarek','tarek')

        self.assertEquals(login_result, True)


    """
    xxxx
    need to finish fake IMAP lib

    # testing single connection
    from BaseConnection import BaseConnectionParams
    my_params = BaseConnectionParams()
    my_params.setParam('HOST', 'localhost')
    my_params.setParam('UserID', 'tarek')
    my_params.setParam('UserPassword', 'tarek')
    my_params.setParam('TYPE', 'IMAP')

    # regular connection
    myconnection = IMAPConnection(my_params)

    if myconnection.login('tarek','tarek'):
        print 'connected to localhost'

        print 'List all folder with attributes and acls'
        for folder in myconnection.list():
            name =  folder['Name']
            print 'Name : ' + name
            print 'Attributes : ' + ' '.join(folder['Attributes'])

            for acl in myconnection.getacl(name):
                print 'Acl : %s has the right %s' %(acl['who'], acl['what'])
            print
        print ''

        print 'making a few message search'
        print myconnection.search('INBOX', None,'SUBJECT','ok')

        myconnection.logout()
        print 'logout'
    else:
        print 'could not connect to locahost'

"""
    # SSL connection
    """
    my_params['SSL'] = 1passwd
    my_params['HOST'] = 'imap.nuxeo.com'
    my_params['PORT'] = 993

    myconnection = IMAPConnection('tarek', my_params)

    import getpass
    password = getpass.getpass()

    # getting server infos
    ssl_socket = myconnection._isSSL()

    print 'Issuer :'+ssl_socket.issuer()
    print 'Server :'+ssl_socket.server()


    if myconnection.login('tziade@nuxeo.com', password):
        print 'connected to imap.nuxeo.com'
        print 'connected to localhost'

        print 'List all folder with attributes and acls'
        for folder in myconnection.list():
            name =  folder['Name']
            print 'Name : ' + name
            print 'Attributes : ' + ' '.join(folder['Attributes'])

            for acl in myconnection.getacl(name):
                print 'Acl : %s has the right %s' %(acl['who'], acl['what'])
            print
        print ''

        print 'making a few message search'
        print myconnection.search('INBOX', None,'SUBJECT','ok')

        myconnection.logout()
        print 'logout'

    """
    """
    # trying a connection collection
    from BaseConnection import ConnectionList

    my_list = ConnectionList()
    my_params = BaseConnectionParams()
    my_params.setParam('HOST', 'localhost')
    my_params.setParam('UserID', 'tarek')
    my_params.setParam('UserPassword', 'tarek')
    my_params.setParam('TYPE', 'IMAP')

    my_list.registerConnectionType('IMAP',makeMailObject)

    sleeper = 3

    # testing respawn
    import time
    for i in range(10) :

        imapob = my_list.getConnection(my_params)

        for folder in imapob.list():
            name =  folder['Name']
            for acl in imapob.getacl(name):
                pass

        imapob.search('INBOX', None,'SUBJECT','ok')
        print 'ends %d with time %d s' %(i, sleeper)
        time.sleep(sleeper)
        sleeper += 1

"""

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(IMAPConnectionTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.imapconnection'),
        ))
