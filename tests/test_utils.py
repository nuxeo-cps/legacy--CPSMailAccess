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
from Testing.ZopeTestCase import ZopeTestCase
from datetime import datetime
from CPSMailAccess.utils import isToday, replyToBody, verifyBody, HTMLize
from basetestcase import MailTestCase

class UtilsTestCase(MailTestCase):

    def test_isToday(self):
        today = datetime(2000, 1, 1)
        today = today.now()
        today_str = today.strftime("%d/%y/%m")

        #self.assert_(isToday(today_str))

    def test_replyToBody(self):
        body = 'voici\r\nun petit message'
        from_ = 'me'
        result = replyToBody(from_, body)
        self.assertEquals(result, '> me wrote\r\n> voici\r\n> un petit message')
        result = replyToBody(from_, body, 'Yo> ')
        self.assertEquals(result, 'Yo> me wrote\r\nYo> voici\r\nYo> un petit message')

    def test_verifyBody(self):
        msg = self.getMailInstance(2)
        verifyBody(msg)

    def test_replyToBodywithHTML(self):
        body = ['Welcome to your cps webmail, webmailtest4 !']
        body.append('')
        body.append('The CPS Team.')
        body = '\r\n'.join(body)
        result = replyToBody('Tarek Ziadé <tz@nuxeo.com>', body)

        result = result.split('\r\n')

        self.assertEqual(result[0], '> Tarek Ziad\xe9 <tz@nuxeo.com> wrote')
        self.assertEqual(result[1], '> Welcome to your cps webmail, webmailtest4 !')
        self.assertEqual(result[2], '> ')
        self.assertEqual(result[3], '> The CPS Team.')

        result = replyToBody('Tarek Ziadé <tz@nuxeo.com>', body)
        result = HTMLize(result)

        result = result.split('<br/>')

        self.assertEqual(result[0], '&gt; Tarek Ziad\xe9 &lt;tz@nuxeo.com&gt; wrote')
        self.assertEqual(result[1], '&gt; Welcome to your cps webmail, webmailtest4 !')
        self.assertEqual(result[2], '&gt; ')
        self.assertEqual(result[3], '&gt; The CPS Team.')




def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UtilsTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.utils'),
        ))
