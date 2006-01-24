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
"""
    This unit test is intended to check that
    there's no regression when installing
    CPSMailAccess from scratch
"""
import unittest
from Testing.ZopeTestCase import installProduct
from Products.CPSDefault.tests.CPSTestCase import CPSTestCase, MANAGER_ID

from Products.ExternalMethod.ExternalMethod import ExternalMethod
from OFS.ObjectManager import BadRequestException

installProduct('Five')
installProduct('CPSMailAccess')

class MailInstallerTestCase(CPSTestCase):

    def afterSetUp(self):
        CPSTestCase.afterSetUp(self)
        self.login(MANAGER_ID)

    def beforeTearDown(self):
        CPSTestCase.beforeTearDown(self)
        self.logout()

    def installProduct(self):
        installer = ExternalMethod('cpsmailaccess_installer', '',
                                   'CPSMailAccess.install', 'install')
        try:
            self.portal._setObject('cpsmailaccess_installer', installer)
        except BadRequestException:
            pass

        upgrader = ExternalMethod('cpsmailaccess_installer', '',
                                   'CPSMailAccess.install', 'upgrade')
        try:
            self.portal._setObject('cpsmailaccess_upgrader', upgrader)
        except BadRequestException:
            pass

    def _installWebmail(self):
        # installing
        self.installProduct()
        self.app.portal.cpsmailaccess_installer(self.app.portal)

    def test_install(self):
        self._installWebmail()
        # updating
        self.app.portal.cpsmailaccess_installer(self.app.portal)

    def test_portlets(self):
        # verify that portlets does not get installed twice
        self._installWebmail()

        self.app.portal.cpsmailaccess_installer(self.app.portal)
        portlets = getattr(self.app.portal.portal_webmail, '.cps_portlets')
        self.assertEquals(len(portlets.objectIds()), 2)

    def test_upgrade(self):

        self._installWebmail()
        self.app.portal.portal_webmail.__version__ = 'upgrade me'

        # updating
        self.app.portal.cpsmailaccess_upgrader(self.app.portal, 'beta2')

        # checking version
        self.assertEquals(self.app.portal.portal_webmail.__version__,
                          (1, 0, 0, 'b2'))

    def test_upgrade2(self):

        self._installWebmail()
        delattr(self.app.portal.portal_webmail, '__version__')

        # updating
        self.app.portal.cpsmailaccess_upgrader(self.app.portal, 'beta2')

        # checking version
        self.assertEquals(self.app.portal.portal_webmail.__version__,
                          (1, 0, 0, 'b2'))

    def test_upgrade_b1_to_b2(self):
        # checking param upgrades
        self._installWebmail()
        pwm = self.app.portal.portal_webmail
        self.assertEquals(pwm.default_connection_params['SSL'], (0, 1))
        del pwm.default_connection_params['SSL']
        delattr(self.app.portal.portal_webmail, '__version__')

        self.app.portal.cpsmailaccess_upgrader(self.app.portal, 'beta2')
        self.assertEquals(pwm.default_connection_params['SSL'], (0, 1))

    def test_paramUpgrade(self):
        self._installWebmail()
        from Products.CPSMailAccess.mailbox import MailBox
        box = MailBox('my_box')
        pwm = self.app.portal.portal_webmail
        pwm._setObject('box_1', box)
        self.app.portal.cpsmailaccess_upgrader(self.app.portal, 'beta2')
        self.assertEquals(pwm.box_1._connection_params['SSL'], (0, 1))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MailInstallerTestCase))
    return suite
