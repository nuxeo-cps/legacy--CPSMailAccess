#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
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
#
# $Id$

import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase

from Products.CPSMailAccess.mailcache import MailCache
from Products.CPSMailAccess.interfaces import IMailMessageCache, IMailMessage
from Products.CPSMailAccess.mailmessage import MailMessage


installProduct('FiveTest')
installProduct('Five')

class MailCacheTestCase(ZopeTestCase):

    def msgKeyGen(self):
        result = 'msg_' + str(self.msg_key)
        self.msg_key += 1
        return result

    def test_putMessage(self):
        """ test putMessage
        """
        ob = MailCache()

        message = MailMessage()
        message.msg_key = 'uniqueid'

        ob.putMessage(message)

        self.assertEquals(len(ob), 1)


        not_a_message = MailCache()
        self.assertRaises(Exception, ob.putMessage, not_a_message)


    def test_retrieveMessage(self):
        """ testing retrieveMessage
        """
        ob = MailCache()

        message = MailMessage()
        message.msg_key = 'uniqueid'

        ob.putMessage(message)

        message = MailMessage()
        message.msg_key = 'uniqueid2'

        ob.putMessage(message)
        self.assertEquals(len(ob), 2)

        result = ob.retrieveMessage('uniqueid', False)
        self.assertNotEquals(result, None)

        result = ob.retrieveMessage('uniqueid2', True)
        self.assertNotEquals(result, None)
        self.assertEquals(len(ob), 1)

        result = ob.retrieveMessage('ssazdzuniqueid2', True)
        self.assertEquals(result, None)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailCacheTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailcache'),
        ))
