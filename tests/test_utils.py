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
from Products.CPSMailAccess.utils import isToday, replyToBody, verifyBody, \
    sanitizeHTML, HTMLize, HTMLToText, decodeHeader, getCurrentDateStr, \
    isValidEmail

from basetestcase import MailTestCase

class UtilsTestCase(MailTestCase):

    def test_isToday(self):
        today = datetime(2000, 1, 1)
        today = today.now()
        today_str = today.strftime("%m/%d/%y")
        self.assert_(isToday(today_str))

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
        # NEED MORE TEST HERE

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


    def test_sanitizeHTML(self):
        html = 'dfghjuik<body> ghfrtgy<script >hj</script>uikolmù</body>'
        res = sanitizeHTML(html)
        self.assertEquals(res, 'dfghjuik ghfrtgyhjuikolm\xf9')

        html = 'dfghjuik&lt;body&gt; ghfrtgy&lt;script &gt;hj&lt;/script&gt;uikolmù&lt;/body&gt;'
        res = sanitizeHTML(html)
        self.assertEquals(res, 'dfghjuik ghfrtgyhjuikolm\xf9')
        html = """<html>
<body>
ezezf<br>
</body>
</html>
"""
        res = sanitizeHTML(html)
        self.assertEquals(res, 'ezezf<br>')

    def test_HTMLToText(self):
        html = 'ezezf<br><span>ezezf</span><br>'
        res = HTMLToText(html)
        self.assertEquals(res, 'ezezf\r\nezezf')

    def oldtest_HTMLToTextNoEffect(self):
        html = """Welcome to your cps webmail, webmailtest4 !

The CPS Team.
"""
        res = HTMLToText(html)
        self.assertEquals(res, """Welcome to your cps webmail, webmailtest4 !

The CPS Team.
""")

    def test_decodeHeader(self):
        # tests unicoding issues
        res = decodeHeader('Tarek Ziadé <webmailtest@nuxeo.com>')
        self.assertEquals(type(res), unicode)
        self.assertEquals(res, u'Tarek Ziadé <webmailtest@nuxeo.com>')

        # japanese encoding
        # XXX need to find better here
        res = decodeHeader('=?iso-2022-jp?Q?8=1B=24B=40iK=7C1=5F=24N3MF=40J=7D=1B=28B?= =?iso-2022-jp?Q?=1B=24BK!!=26=25a=25k=25=5E=25=2C=258=25s=1B=28B?= <delivery@hosyou-r01.mine.nu>')
        self.assertEquals(type(res), unicode)
        self.assertEquals(res, u'8\x1b$B@iK|1_$N3MF@J}\x1b(B\x1b$BK!!&%a%k%^%,%8%s\x1b(B<delivery@hosyou-r01.mine.nu>')

    def test_getCurrentDateStr(self):
        date = getCurrentDateStr()


    def test_isValidEmail(self):
        self.assert_(isValidEmail('tz@nuxeo.com'))
        self.assert_(not isValidEmail('tarek@nuxeo.comfmm'))
        self.assert_(not isValidEmail('tarek_AT_nuxeo.commm'))
        self.assert_(not isValidEmail('fezefz'))
        self.assert_(not isValidEmail(''))
        self.assert_(isValidEmail('tdddd.dddddd.ddd@nu.x.eo.com'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UtilsTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.utils'),
        ))
