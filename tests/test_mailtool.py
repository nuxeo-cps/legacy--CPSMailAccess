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

from basetestcase import MailTestCase

from Products.CPSMailAccess.mailtool import MailTool
from Products.CPSMailAccess.interfaces import IMailTool


class MailToolTestCase(MailTestCase):
    def test_base(self):
        # single instance
        ob = MailTool()
        self.assertNotEquals(ob, None)
        self.assertEquals(ob.getId(), 'portal_webmail')

    def test_listConnectionTypes(self):
        # testing list connection types
        ob = MailTool()
        ct = ob.listConnectionTypes()
        self.assertNotEquals(ct , [])

    def test_boxcreation(self):
        ob = MailTool()
        ob.addMailBox('tarek')
        ob.addMailBox('bill')
        self.assert_(hasattr(ob, 'box_tarek'))
        self.assert_(hasattr(ob, 'box_bill'))
        ob.deleteMailBox('bill')
        self.assert_(not hasattr(ob, 'box_bill'))

    def test_getConnection(self):
        ob = MailTool()
        connection_params = {'uid' : 'admin', 'connection_type' : 'DUMMY'}

        # regular connector
        one = ob.getConnection(connection_params)

        # second connector
        two = ob.getConnection(connection_params, 1)

        one_test = ob.getConnection(connection_params)
        two_test = ob.getConnection(connection_params, 1)

        self.assertNotEquals(id(one), id(two))
        self.assertEquals(id(one), id(one_test))
        self.assertEquals(id(two), id(two_test))

    def test_getMailDeliverer(self):
        mailbox = self._getMailBox()
        portal_webmail = mailbox.portal_webmail
        del portal_webmail.default_connection_params['maildir']
        mail_deliverer = portal_webmail.getMailDeliverer()
        self.assertNotEquals(mail_deliverer, None)

    def test_canHaveMailBox(self):
        class FakeUser:
            def __init__(self, uid):
                self.uid = uid

            def getProperty(self, *args, **kw):
                if self.uid == 'CPSTestCase':
                    return 1
                else:
                    return 0

            def getId(self):
                return self.uid

        class FakeMemberShip:
            def getMemberById(self, uid):
                if uid not in ('CPSTestCase', 'CPSTestCase2'):
                    return None
                else:
                    return FakeUser(uid)

        mailbox = self._getMailBox()
        self.portal.portal_membership = FakeMemberShip()

        portal_webmail = mailbox.portal_webmail
        self.assert_(portal_webmail.canHaveMailBox('CPSTestCase'))
        self.assert_(not portal_webmail.canHaveMailBox('IDONTEXIST'))

    def test_secu(self):
        def canHaveMailBox(*args, **kw):
            return True

        class FakeMemberShip:
            def getAuthenticatedMember(self):
                return None

        self.portal.portal_membership = FakeMemberShip()
        mailbox = self._getMailBox()
        portal_webmail = mailbox.portal_webmail
        checker = portal_webmail._checkCanSendMails
        from AccessControl import Unauthorized
        self.assertRaises(Unauthorized, checker)

        portal_webmail.canHaveMailBox = canHaveMailBox

        # should be fine now
        checker

    def test_Interface(self):
        # make sure the contract is respected
        from zope.interface.verify import verifyClass
        self.failUnless(verifyClass(IMailTool, MailTool))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailToolTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailtool'),
        ))
