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
from types import StringType, ListType
import unittest, os
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase, _print

from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailmessageview import MailMessageView
from Products.CPSMailAccess.interfaces import IMailMessage
from Products.CPSMailAccess.mailmessageview import MailMessageView

from Products.CPSMailAccess.tests import __file__ as landmark

from basetestcase import MailTestCase

def openfile(filename, mode='r'):
    path = os.path.join(os.path.dirname(landmark), 'data', filename)
    return open(path, mode)


class MailMessageViewTestCase(MailTestCase):

    def test_MailMessageViewInstance(self):
        # testing view instanciation
        ob = self.getMailInstance(6)
        view = MailMessageView(ob, None)
        self.assertNotEquals(view, None)

    def test_MailMessageHeaders(self):
        # testing view instanciation
        ob = self.getMailInstance(6)
        view = MailMessageView(ob, None)

        self.assertEquals(view.renderFromList(),
            'Barry <barry@digicool.com>')

        self.assertEquals(view.renderToList(),
            'Dingus Lovers <cravindogs@cravindogs.com>')

        ob = MailMessage()
        ob.cache_level = 2
        view = MailMessageView(ob, None)

        self.assertEquals(view.renderFromList(), '?')

        self.assertEquals(view.renderToList(), '?')

    def test_MailMessageparts(self):
        # testing message parts
        ob = self.getMailInstance(1)
        body = ob.getPart(0)

        self.assertNotEquals(body, '')
        self.assertNotEquals(body, None)
        view = MailMessageView(ob, None)
        viewbody = view.renderBody()
        full = body.as_string()
        self.assertNotEquals(full.find('http://www.zzz.org/mailman/listinfo/ppp'), -1)

    def test_MailMessageViewMethods(self):

        ob = self.getMailInstance(6)
        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)
        """
        view.reply()
        view.reply_all()
        view.forward()
        view.delete()
        """

    def test_renderMailList(self):
        # render mail list calls folder's view
        mailbox = self._getMailBox()
        mailbox._addMessage('msg1' , 'i-love-pizzas-with-fresh-tomatoes')
        mailbox._addMessage('msg2' , 'i-love')
        msg2_view = MailMessageView(getattr(mailbox, '.msg2'), self.request)

        ml = msg2_view.renderMailList()
        self.assertEquals(len(ml), 2)

    def test_renderDate(self):
        ob = self.getMailInstance(6)
        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)

        date = view.renderDate()
        self.assertEquals(date, 'Fri 20/04/01 19:35')

    def test_attachedfiles(self):
        ob = self.getMailInstance(6)
        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)

        files = view.attached_files()
        self.assertEquals(len(files), 1)
        self.assertEquals(len(files[0]), 1)
        file = files[0][0]
        self.assertEquals(file['mimetype'], 'image/gif')
        self.assertEquals(file['filename'], 'dingusfish.gif')



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessageview'),
        ))
