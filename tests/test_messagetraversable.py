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
import unittest, os
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
from Products.CPSMailAccess.interfaces import IMessageTraverser, IMailMessage
from Products.CPSMailAccess.messagetraversable import MessageTraversable
from Products.CPSMailAccess.mailmessage import MailMessage
from CPSMailAccess.mailtool import manage_addMailTool, MailTool
from CPSMailAccess.mailbox import manage_addMailBox

installProduct('FiveTest')
installProduct('Five')

from CPSMailAccess.tests import __file__ as landmark
from Acquisition import Implicit

def openfile(filename, mode='r'):
    path = os.path.join(os.path.dirname(landmark), 'data', filename)
    return open(path, mode)


class FakePortal(Implicit):
    def this(self):
        return self

    def _setObject(self, id, ob):
        setattr(self, id, ob)

    def getPhysicalPath(self):
        return ('http://nowhere',)

fakePortal = FakePortal()
portal_webmail = MailTool()
fakePortal.portal_webmail = portal_webmail


class FakeRequest:

    maybe_webdav_client = False

    def getPresentationSkin(self):
        return None

    def get(self, element1, element2):
        return ''


class MessageTraversableTestCase(ZopeTestCase):

    def __init__(self, methodName='runTest'):
        ZopeTestCase.__init__(self, methodName)
        self.portal = fakePortal

    def _getMailBox(self):
        """ testing connector getter
        """
        container = fakePortal
        manage_addMailBox(container, 'INBOX')
        mailbox = self.portal.INBOX
        mailbox.connection_params['uid'] = 'tziade'
        mailbox.connection_params['connection_type'] = 'IMAP'
        mailbox.connection_params['password'] = 'secret'
        mailbox.connection_params['HOST'] = 'localhost'
        return mailbox

    def _msgobj(self, filename):
        fp = openfile(filename)
        try:
            data = fp.read()
        finally:
            fp.close()

        return data

    def getMailInstance(self,number):
        ob = MailMessage()
        ob.cache_level = 2

        if number < 9:
            data = self._msgobj('msg_0'+str(number+1)+'.txt')
        else:
            data = self._msgobj('msg_'+str(number+1)+'.txt')

        ob.loadMessage(data)
        return ob

    def test_SimpleInstance(self):
        # mailmessageedit view
        ob = MailMessage('ok')
        mt = MessageTraversable(ob)
        self.assert_(mt)
        return mt

    def test_traverse(self):

        req = FakeRequest()
        ob = MailMessage('ok')
        ob.REQUEST = req

        # testing hasattr
        ob2 = MailMessage('sub_message')
        ob.sub_message = ob2
        mt = MessageTraversable(ob)
        result = mt.traverse('sub_message', req)
        self.assertEquals(result.getId(), 'sub_message')

    def test_adaptPart(self):
        req = FakeRequest()
        ob = self.getMailInstance(7)
        part = ob.getPart(0)

        mt = MessageTraversable(ob)
        msg = mt.adaptPart(0, part)

        self.assert_(msg)

        ob2 = MailMessage('ob2')
        ob2.cache_level = 2
        ob2.loadMessage(part.as_string())

        self.assertEquals(ob2.getRawMessage(), msg.getRawMessage())


    def test_onthefly(self):
        # testing on the fly creation
        container = self._getMailBox()
        req = FakeRequest()

        ob = self.getMailInstance(7)
        ob.parent_folder = container

        ob.persistent_parts = (1, 3)
        mt = MessageTraversable(ob)
        result = mt.traverse('', req)
        self.assert_(result)

        # give me the first part please
        result = mt.traverse('1', req)
        self.assert_(result)

        result = mt.traverse('2', req)

        self.assertNotEquals(result, None)

        result = mt.traverse('3', req)
        self.assert_(result)

        result = mt.traverse('4', req)
        self.assert_(result)

    def test_filename(self):
        # testing filename traverse
        req = FakeRequest()
        ob = self.getMailInstance(6)
        ob.persistent_parts = (1, 3)
        mt = MessageTraversable(ob)
        result = mt.traverse('dingusfish.gif', req)
        self.assert_(result)

    def test_loadParts(self):
        # testing part loading
        mailbox = self._getMailBox()
        mailbox._addMessage('msg1' , 'i-love-pizzas-with-fresh-tomatoes')
        ob = self.getMailInstance(6)

        msg1 = getattr(mailbox, '.msg1')
        msg1.cache_level = 2

        msg1.loadMessage(ob.getRawMessage())

        msg1.loadPart(2, volatile=True)

### TODO :  test parts of parts

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MessageTraversableTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.messagetraversable'),
        ))