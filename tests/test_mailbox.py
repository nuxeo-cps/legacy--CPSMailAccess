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

from Products.CPSMailAccess.mailbox import MailBox, MailBoxParametersView
from Products.CPSMailAccess.interfaces import IMailBox


installProduct('FiveTest')
installProduct('Five')

class MailBoxTestCase(ZopeTestCase):

    msg_key = 0

    def msgKeyGen(self):
        result = 'msg_' + str(self.msg_key)
        self.msg_key += 1
        return result

    def test_base(self):
        """ single instance
        """
        ob = MailBox('mailbox')
        self.assertNotEquals(ob, None)

    def test_MailBoxParametersView(self):
        """ testing MailBoxParametersView generators
        """
        mailbox = MailBox('mailbox')

        view = MailBoxParametersView(mailbox, None)

        self.assertNotEquals(view, None)

        params = view._getParameters()
        self.assertNotEquals(params, [])

        params = view.renderParameters()
        self.assertNotEquals(params, '')

        params = view.renderParametersForm()
        self.assertNotEquals(params, '')

        params = view.renderAddParamForm()
        self.assertNotEquals(params, '')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailBoxTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailbox'),
        ))
