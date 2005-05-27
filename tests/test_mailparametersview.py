#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2005 Nuxeo SARL <http://nuxeo.com>
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
from Products.CPSMailAccess.mailparameterviews import MailBoxParametersView
from basetestcase import MailTestCase

class MailParamsTestCase(MailTestCase):

    def test_MailBoxParametersView(self):
        # testing MailBoxParametersView generators
        mailbox = self._getMailBox()
        view = MailBoxParametersView(mailbox, None)
        self.assertNotEquals(view, None)

        params = view._getParameters()
        self.assertNotEquals(params, [])

        params = view.renderParameters()
        self.assertNotEquals(params, '')

        params = view.renderParametersForm()
        self.assertNotEquals(params, '')

    def test_computeRequest(self):
        # testing MailBoxParametersView parameters interface
        mailbox = self._getMailBox()
        view = MailBoxParametersView(mailbox, None)
        params = {'connection_type' : 'DUMMY', 'uid' : 'tarek', 'ok': '12',
                  'submit' : 'ok'}

        computed = view._computeRequest(params)
        self.assertEquals(computed, {'connection_type' : ('DUMMY', 1),
                                     'uid' : ('tarek', 1), 'ok': ('12', 1)})

        params = {'connection_type' : 'DUMMY', 'uid' : 'tarek', 'ok': '12',
                  'submit' : 'ok', 'secu_connection_type' : 0, 'secu_ok': 0}

        computed = view._computeRequest(params)
        self.assertEquals(computed, {'connection_type' : ('DUMMY', 0),
                                     'uid' : ('tarek', 1), 'ok': ('12', 0)})

        params = {'connection_type' : 'DUMMY', 'uid' : 'tarek', 'ok': '12',
                  'submit' : 'ok', 'secu_connection_type' : 'on', 'secu_ok': ''}

        computed = view._computeRequest(params)
        self.assertEquals(computed, {'connection_type' : ('DUMMY', 1),
                                     'uid' : ('tarek', 1), 'ok': ('12', 0)})


    def test_MailBoxParametersInterface(self):
        # testing MailBoxParametersView parameters interface
        mailbox = self._getMailBox()
        view = MailBoxParametersView(mailbox, None)
        params = {'connection_type' : 'DUMMY', 'uid' : 'tarek', 'ok': '12',
                  'submit' : 'ok'}

        view.setParameters(params)
        self.assertEquals(mailbox.getConnectionParams()['ok'], '12')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailParamsTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailparameterviews'),
        ))
