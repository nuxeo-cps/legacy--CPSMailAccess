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
import os, sys
from Products.CPSMailAccess.connectionlist import ConnectionList
import fakeimaplib
if sys.modules.has_key('imaplib'):
    del sys.modules['imaplib']
sys.modules['imaplib'] = fakeimaplib

from Products.CPSMailAccess.imapconnection import IMAPConnection
from time import time,sleep
from basetestcase import MailTestCase

fake_imap_enabled  = 1


"""
    xxxx
    need to finish fake IMAP lib
"""
class IMAPConnectionTestCase(MailTestCase):

    old_uimaplib = None

    def makeConnection(self):
        my_params = {}
        my_params['HOST'] = 'localhost'
        my_params['UserID'] = 'tarek'
        my_params['UserPassword'] = 'tarek'
        my_params['TYPE'] = 'IMAP'
        myconnection = IMAPConnection(my_params)
        return myconnection

    def test_Instance(self):
        # testing simple instanciation with parameters
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
        # testing simple SSL instanciation with parameters
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
        # testing simple instanciation with missing parameters
        from Products.CPSMailAccess.baseconnection import ConnectionParamsError
        my_params = {}

        self.failUnlessRaises(ConnectionParamsError, IMAPConnection, my_params)

    def test_login(self):
        # testing simple instanciation with missing parameters
        ob = self.makeConnection()
        login_result = ob.login('tarek','tarek')
        self.assertEquals(login_result, True)

    def test_partQueriedList(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        res = ob.partQueriedList('(FLAGS RFC822.SIZE RFC822.HEADER)')
        self.assertEquals(res, ['FLAGS', 'RFC822.SIZE', 'RFC822.HEADER'])

        res = ob.partQueriedList('(')
        self.assertEquals(res, [])

    def test_extractresults(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        fullquery = '(FLAGS RFC822.SIZE RFC822.HEADER)'
        res = ob._extractResult('FLAGS',
        [('1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'), ')'])
        self.assertEquals(res, ['Seen'])

        res = ob._extractResult('RFC822.SIZE', [('1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'), ')'])
        self.assertEquals(res, '515')

        res = ob._extractResult('RFC822.HEADER', ['1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'])

        self.assertEquals(res, {'Received': '(qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000', 'Delivered-To': 'webmaster@openconference.org', 'From': 'webmaster@openconference.org', 'Return-Path': '<webmaster@zopeur.org>', 'Content-Transfer-Encoding': '8bit', 'To': 'webmaster@openconference.org', 'Mime-Version': '1.0', 'Date': 'Sat, 01 Jan 2005 02:31:52 +0100', 'Message-ID': '<20050101013152.24339.qmail@ns2641.ovh.net>', 'Content-Type': 'text/plain; format=flowed; charset="iso-8859-1"', 'Subject': 'webmaster@openconference.org'})



    def test_infoExtraction(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        results = ob.fetch(box, 1, '(FLAGS RFC822.SIZE RFC822.HEADER)')

        self.assertEquals(results[0], ['Seen'])
        self.assertEquals(results[1], '515')



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(IMAPConnectionTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.imapconnection'),
        ))
