#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
from basetestcase import MailTestCase

from Products.CPSMailAccess.mailfiltering import MailFiltering, ZODBMailBackEnd

class MailFilteringTestCase(MailTestCase):

    def __init__(self, methodName='runTest'):
        MailTestCase.__init__(self, methodName)

    def test_instanciate(self):
        ob = MailFiltering()
        self.assertNotEquals(ob, None)

    def test_addFilter(self):
        ob = MailFiltering()
        ob.addFilter('subjet', 'condition', 'value', 'action', 'action_param')
        self.assertEquals(len(ob._filters), 1)
        ob.addFilter('subjet', 'condition', 'value', 'action2', 'action_param')
        self.assertEquals(len(ob._filters), 1)
        ob.addFilter('subjet', 'condition', 'valuze', 'action2', 'action_param')
        ob.addFilter('subjet', 'condition', 'vaalue', 'action2', 'action_param')
        self.assertEquals(len(ob._filters), 3)

    def test_delFilter(self):
        ob = MailFiltering()
        ob.addFilter('subjet', 'condition', 'value', 'action', 'action_param')
        ob.delFilter('subjet', 'condition', 'value', 'action', 'action_param')
        self.assertEquals(len(ob._filters), 0)
        ob.delFilter('subjet', 'condition', 'value', 'action', 'action_param')
        self.assertEquals(len(ob._filters), 0)

    def test_matchCondition(self):
        ob = MailFiltering()
        self.assert_(ob._matchCondition('i have a cool usbkey', 1, 'cool'))
        self.assert_(not ob._matchCondition('i have a cool usbkey', 1, 'codol'))

        self.assert_(not ob._matchCondition('i have a cool usbkey', 2, 'cool'))
        self.assert_(ob._matchCondition('i have a cool usbkey', 2, 'codol'))

        self.assert_(not ob._matchCondition('i have a cool usbkey', 3, 'we do'))
        self.assert_(ob._matchCondition('i have a cool usbkey', 3, ' i have'))

        # testing with brackets
        self.assert_(not ob._matchCondition('[Dev] i have a cool usbkey', 3, '[devel]'))
        self.assert_(ob._matchCondition('[EuroPython] i have a cool usbkey', 3, '[EuroPython]'))


        self.assert_(not ob._matchCondition('i have a cool usbkey', 4, 'keys'))
        self.assert_(ob._matchCondition('i have a cool usbkey', 4, 'key '))

        self.assert_(ob._matchCondition('i have a cool usbkey', 5,
                                            ' i have a cool usbkey  '))
        self.assert_(ob._matchCondition('i have a cool usbkey', 5,
                                        'i have a cool usbkey'))
        self.assert_(not ob._matchCondition('i have a cool usbkey', 5, 'key '))

        self.assert_(ob._matchCondition('i have a cool usbkey', 6, 'key '))
        self.assert_(not ob._matchCondition('i have a cool usbkey', 6,
                                            ' i have a cool usbkey  '))

    def test_matchConditionMail(self):
        # for extact matches when value looks like a mail
        # we try to extract nude email or name
        ob = MailFiltering()
        self.assert_(ob._matchCondition('Tarek Ziadé <tz@nuxeo.com>', 5,
                                        'tz@nuxeo.com'))

        self.assert_(ob._matchCondition('Tarek Ziadé <tz@nuxeo.com>', 5,
                                        'Tarek Ziadé'))

    def headerEnconding(self):
        ob = MailFiltering()
        self.assert_(ob._matchCondition(u'Tarek Ziad\xe9', 5,
                     '=?iso-8859-1?q?Tarek_Ziad=e9?='))

    def test_filterMatches(self):
        # now testing the real message filtering
        ob = MailFiltering()

        msg = self.getMailInstance(0)
        msg2 = self.getMailInstance(1)
        element = {}

        element['subject'] = 'Subject'
        element['condition'] = 1
        element['value'] = 'test'

        self.assert_(ob._filterMatches(element, msg))
        self.assert_(not ob._filterMatches(element, msg2))

        element['value'] = 'digest'

        self.assert_(not ob._filterMatches(element, msg))
        self.assert_(ob._filterMatches(element, msg2))

        element['condition'] = 2
        element['value'] = 'test'

        self.assert_(not ob._filterMatches(element, msg))
        self.assert_(ob._filterMatches(element, msg2))

        element['value'] = 'digest'

        self.assert_(ob._filterMatches(element, msg))
        self.assert_(not ob._filterMatches(element, msg2))

        element['condition'] = 3
        element['value'] = 'This IS a'
        self.assert_(ob._filterMatches(element, msg))
        self.assert_(not ob._filterMatches(element, msg2))

        element['condition'] = 4
        element['value'] = 'message'
        self.assert_(ob._filterMatches(element, msg))
        self.assert_(not ob._filterMatches(element, msg2))

    def test_actionFilter(self):
        ob = MailFiltering()
        msg = self.getMailInstance(0)
        element = {}

        self.assertEquals(msg.isjunk, 0)

        # if subject contains test it's a junk
        element['subject'] = 'Subject'
        element['condition'] = 1
        element['value'] = 'test'
        element['action'] = 4
        element['action_param'] = 1

        ob._actionFilter(element, msg)
        self.assertEquals(msg.isjunk, 1)

        # if subject contains test it's a junk
        # we append the label'TEST'
        element['action'] = 3
        element['action_param'] = 'TEST'
        ob._actionFilter(element, msg)
        self.assertEquals(msg.getHeader('Subject')[0],
                          '[TEST] This is a test message')

        # if subject contains test we move it to test folder
        mailbox = self._getMailBox()
        tests = mailbox._addFolder('tests', 'INBOX.tests')
        msg1 = mailbox._addMessage('1', '1')
        self.assertEquals(len(mailbox.objectIds()), 2)
        self.assertEquals(len(tests.objectIds()), 0)

        msg1.setHeader('Subject', 'This is a test message')

        element['action'] = 1
        element['action_param'] = 'INBOX.tests'

        ob._actionFilter(element, msg1)

        # checks that the message has been moved to tests folder
        self.assertEquals(len(mailbox.objectIds()), 1)
        self.assertEquals(len(tests.objectIds()), 1)

        element['action'] = 2
        element['action_param'] = 'INBOX.tests.tests'

        self.assertEquals(len(tests.objectIds()), 1)

         # checks that the message has been moved to ttests folder
        ttests = tests._addFolder('tests', 'INBOX.tests.tests')
        self.assertEquals(len(tests.objectIds()), 2)

        element['action_param'] = 'INBOX.tests.tests'

        ob._actionFilter(element, tests['.1'])

        self.assertEquals(len(tests.objectIds()), 2)
        self.assertEquals(len(ttests.objectIds()), 1)

    def test_moveFilter(self):
        ob = MailFiltering()
        ob.addFilter('subjet', 'condition', 'value', 'action', 'action_param')
        ob.addFilter('subjet', 'condition', 'vaezrlue', 'action2', 'action_param')
        ob.addFilter('subjet', 'condition', 'valuze', 'action2', 'action_param')
        self.assertEquals(len(ob._filters), 3)

        self.assertEquals(ob._filters[2]['value'], 'valuze')
        ob.moveFilter(2,  0)
        self.assertEquals(ob._filters[1]['value'], 'valuze')
        ob.moveFilter(1,  0)
        self.assertEquals(ob._filters[0]['value'], 'valuze')

    def test_moveFilterPersistent(self):

        ob = MailFiltering(ZODBMailBackEnd())
        ob.addFilter('subjet', 'condition', 'value', 'action', 'action_param')
        ob.addFilter('subjet', 'condition', 'vaezrlue', 'action2', 'action_param')
        ob.addFilter('subjet', 'condition', 'valuze', 'action2', 'action_param')
        self.assertEquals(len(ob._filters), 3)

        self.assertEquals(ob._filters[2]['value'], 'valuze')
        ob.moveFilter(2,  0)
        self.assertEquals(ob._filters[1]['value'], 'valuze')
        ob.moveFilter(1,  0)
        self.assertEquals(ob._filters[0]['value'], 'valuze')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailFilteringTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailfiltering'),
        ))
