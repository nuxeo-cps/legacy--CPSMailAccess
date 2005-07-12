#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (C) 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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
import unittest, os
from Testing import ZopeTestCase
from Testing.ZopeTestCase import installProduct, _print
from Products.CPSDefault.tests import CPSTestCase

from AccessControl.SecurityManagement \
    import newSecurityManager, noSecurityManager

from Products.ExternalMethod.ExternalMethod import ExternalMethod
from OFS.ObjectManager import BadRequestException

installProduct('Five')
installProduct('CPSMailAccess')

class MailInstallerTestCase(CPSTestCase.CPSTestCase):

    def _setup(self):
        if self._configure_portal:
            self.login()

    def login(self):
        uf = self.app.acl_users
        user = uf.getUserById('CPSTestCase').__of__(uf)
        newSecurityManager(None, user)

    def logout(self):
        noSecurityManager()
        get_transaction().commit()

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
        self.app.portal.cpsmailaccess_installer()

    def test_install(self):
        self._installWebmail()
        # updating
        self.app.portal.cpsmailaccess_installer()

    def test_portlets(self):
        # verify that portlets does not get installed twice
        self._installWebmail()

        self.app.portal.cpsmailaccess_installer()
        portlets = getattr(self.app.portal.portal_webmail, '.cps_portlets')
        self.assertEquals(len(portlets.objectIds()), 2)

    def test_upgrade(self):

        self._installWebmail()
        self.app.portal.portal_webmail.__version__ = 'upgrade me'

        # updating
        self.app.portal.cpsmailaccess_upgrader('beta2')

        # checking version
        self.assertEquals(self.app.portal.portal_webmail.__version__,
                          (1, 0, 0, 'b2'))

    def test_upgrade2(self):

        self._installWebmail()
        delattr(self.app.portal.portal_webmail, '__version__')

        # updating
        self.app.portal.cpsmailaccess_upgrader('beta2')

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

        self.app.portal.cpsmailaccess_upgrader('beta2')
        self.assertEquals(pwm.default_connection_params['SSL'], (0, 1))


class MailInstaller(CPSTestCase.CPSInstaller):

    def install(self, portal_id):
        self.addUser()
        self.login()
        self.addPortal(portal_id)
        self.fixupTranslationServices(portal_id)
        self.logout()

def setupPortal(PortalInstaller=MailInstaller):
    # Create a CPS site in the test (demo-) storage
    app = ZopeTestCase.app()
    # PortalTestCase expects object to be called "portal", not "cps"
    if hasattr(app, 'portal'):
        app.manage_delObjects(['portal'])
    MailInstaller(app).install('portal')

setupPortal(MailInstaller)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailInstallerTestCase),
        ))
