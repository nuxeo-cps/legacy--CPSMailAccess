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
from Testing.ZopeTestCase import _print
from Products.CPSMailAccess.mailrenderer import MailRenderer
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.interfaces import IMailRenderer
from Products.CPSMailAccess.mailtool import MailTool
from Products.CPSMailAccess.mailbox import manage_addMailBox
from CPSMailAccess.tests import __file__ as landmark
from email.Errors import BoundaryError
from basetestcase import MailTestCase


class MailRendererTestCase(MailTestCase):

    def fakePhysicalPath(self):
        #
        return ('', 'http://ok/path')

    def getAllMails(self):
        res = []
        for i in range(35):
            ob = MailMessage()
            ob.cache_level = 2
            if i < 9:
                data = self._msgobj('msg_0'+str(i+1)+'.txt')
            else:
                data = self._msgobj('msg_'+str(i+1)+'.txt')

            if data <> '':
                ob.loadMessage(data)
                res.append(ob)
        return res

    def getMailInstance(self,number):
        ob = MailMessage()
        ob.cache_level = 2

        if number < 9:
            data = self._msgobj('msg_0'+str(number+1)+'.txt')
        else:
            data = self._msgobj('msg_'+str(number+1)+'.txt')

        ob.loadMessage(data)
        return ob

    def test_simpleInstanciation(self):
        # testing simple instanciation
        ob = MailRenderer()
        self.assertNotEquals(ob, None)

    def test_bodyRendering(self):
        # testing the simplest mail structure
        mail = self.getMailInstance(0)
        box = self._getMailBox()
        box._setObject('mail', mail)
        mail = box.mail
        ob = MailRenderer()
        rendered = ob.renderBody(mail)
        self.assertNotEqual(rendered, '')
        self.assertNotEqual(rendered, None)
        self.assertEquals(rendered, '<br/>Hi,<br/><br/>Do you like this message?<br/><br/>-Me<br/>')

    def test_bodyRendering2(self):
        # testing a mail with an attached file
        mail = self.getMailInstance(6)
        box = self._getMailBox()
        box._setObject('mail2', mail)
        mail = box.mail2
        ob = MailRenderer()
        rendered = ob.renderBody(mail)
        self.assertNotEqual(rendered, '')
        self.assertNotEqual(rendered, None)
        self.assertEquals(rendered, 'Hi there,<br/><br/>This is the dingus fish.<br/>')

    def test_allRendering(self):
        # testing all mails with MIME engine
        ob = MailRenderer()
        for i in range(35):
            mail = self.getMailInstance(i)
            # need soem acquisition here
            container = self._getMailBox()
            container._setObject('my_mail'+str(i), mail)
            mail = getattr(container, 'my_mail'+str(i))
            rendered = ob.renderBody(mail)
            # see here for deeper checks on rendered body
            self.assertNotEqual(rendered, None)

    def test_badbodyrender(self):
        ob = MailRenderer()

        res = ob.render(None,'charset=iso88-59-15', None)
        self.assertEquals(res, '')

    def test_unicode(self):

        ob = MailRenderer()

        res = ob.render('ééé','charset=iso8859-15;type=text/plain', None)
        self.assertEquals(res, u'\xe9\xe9\xe9')

        # wrong chartset given,(it happens folks, it happens)
        res = ob.render('ééé','type=text/plain;charset=us/ascii', None)
        self.assertEquals(res, u'\xe9\xe9\xe9')

    def test_multipartAlternativeReadLotus(self):
        # lotus note mail message
        # the body gets empty in the view
        # added this test
        ob = self.getMailInstance(35)
        rd = MailRenderer()

        ob.getPhysicalPath = self.fakePhysicalPath

        body = rd.renderBody(ob, 0)

        self.assertNotEquals(body, '')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailRendererTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailrenderer'),
        ))
