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

import unittest, os
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase, _print

from Products.CPSMailAccess.mailrenderer import MailRenderer
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.interfaces import IMailRenderer

from CPSMailAccess.tests import __file__ as landmark

installProduct('FiveTest')
installProduct('Five')

def openfile(filename, mode='r'):
    path = os.path.join(os.path.dirname(landmark), 'data', filename)
    return open(path, mode)

class MailRendererTestCase(ZopeTestCase):

    def _msgobj(self, filename):
        try:
            fp = openfile(filename)
            try:
                data = fp.read()
            finally:
                fp.close()

            return data
        except IOError:
             # this is a warning when mail test file is missing
             _print('\n!!!!!!!!!!!!!!!!!!!!!!'+ str(filename) +
                 ' not found for MailRendererTestCase')
             return ''

    def getAllMails(self):
        res = []
        for i in range(35):
            ob = MailMessage()
            if i < 9:
                data = self._msgobj('msg_0'+str(i+1)+'.txt')
            else:
                data = self._msgobj('msg_'+str(i+1)+'.txt')

            if data <> '':
                try:
                    ob.loadMessage(data)
                    res.append(ob)
                except:
                    pass
        return res

    def getMailInstance(self,number):
        ob = MailMessage()

        if number < 9:
            data = self._msgobj('msg_0'+str(number+1)+'.txt')
        else:
            data = self._msgobj('msg_'+str(number+1)+'.txt')

        ob.loadMessage(data)
        return ob

    def test_simpleInstanciation(self):
        """ testing simple instanciation
        """
        ob = MailRenderer()
        self.assertNotEquals(ob, None)

    def test_bodyRendering(self):
        """ testing the simplest mail structure
        """
        mail = self.getMailInstance(0)
        ob = MailRenderer()
        part = mail.getPart()
        rendered = ob.renderBody(mail)
        self.assertNotEqual(rendered, '')
        self.assertNotEqual(rendered, None)
        self.assertEquals(rendered, '\nHi,\n\nDo you like this message?\n\n-Me\n')


    def test_bodyRendering(self):
        """ testing a mail with an attached file
        """
        mail = self.getMailInstance(6)
        ob = MailRenderer()
        part = mail.getPart()
        rendered = ob.renderBody(mail)
        self.assertNotEqual(rendered, '')
        self.assertNotEqual(rendered, None)
        self.assertEquals(rendered, 'Hi there,\n\nThis is the dingus fish.\n')

    def test_allRendering(self):
        """ testing all mails with MIME engine
        """
        ob = MailRenderer()
        for i in range(35):
            mail = self.getMailInstance(i)

            # for multiparts, just get first part
            #raise str(mail)
            part = mail.getPart()

            rendered = ob.renderBody(mail)

            # see here for deeper checks on rendered body
            self.assertNotEqual(rendered, None)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailRendererTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailrenderer'),
        ))
