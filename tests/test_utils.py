#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import ZopeTestCase
from datetime import datetime
from Products.CPSMailAccess.utils import *
from basetestcase import MailTestCase

class UtilsTestCase(MailTestCase):

    total = 0

    def method(self, arg1, arg2):
        self.total = arg1 + arg2

    def addOne(self):
        self.total += 1

    def test_isToday(self):
        today = datetime(2000, 1, 1)
        today = today.now()
        today_str = today.strftime("%m/%d/%y")
        self.assert_(isToday(today_str))

    def test_replyToBody(self):
        body = 'voici\r\nun petit message'
        from_ = 'me'
        result = replyToBody(from_, body)
        self.assertEquals(result, u'> me wrote\r\n> voici\r\n> un petit message')

        result = replyToBody(from_, body, 'Yo> ')
        self.assertEquals(result, u'Yo> me wrote\r\nYo> voici\r\nYo> un petit message')

        body = 'voici\r\nun petit mes�������sage'
        from_ = 'm�'
        result = replyToBody(from_, body)
        self.assertEquals(result, u'> m\xe9 wrote\r\n> voici\r\n> un petit mes\xe9\xe9\xe9\xe9\xe9\xe9\xe9sage')

    def test_removeHTML(self):
        body = u'voici un petit message avec <b>html</b> <a href="#">a</a>'
        result = removeHTML(body)
        self.assertEquals(result, u'voici un petit message avec html a')

    def test_replyToBodyClean(self):
        body = 'voici\r\nun petit message avec <b>html</b> <a href="#">a</a>'
        from_ = 'me'
        result = replyToBody(from_, body)
        self.assertEquals(result, u'> me wrote\r\n> voici\r\n> un petit message avec html a')

    def test_replyToBodyClean2(self):
        body = 'voici\r\nun petit message avec <b>html</b> <a href="#">a</a>'
        from_ = '<a href="mailto">tz@nuxeo.com</a>'
        result = replyToBody(from_, body)
        self.assertEquals(result, u'> tz@nuxeo.com wrote\r\n> voici\r\n> un petit message avec html a')

    def test_verifyBody(self):
        msg = self.getMailInstance(2)
        verifyBody(msg)
        # NEED MORE TEST HERE

    def test_replyToBodywithHTML(self):
        body = ['Welcome to your cps webmail, webmailtest4 !']
        body.append('')
        body.append('The CPS Team.')
        body = '\r\n'.join(body)
        result = replyToBody('Tarek Ziad� <tz@nuxeo.com>', body)

        result = result.split('\r\n')

        self.assertEqual(result[0], u'> Tarek Ziad\xe9 wrote')
        self.assertEqual(result[1], u'> Welcome to your cps webmail, webmailtest4 !')
        self.assertEqual(result[2], u'> ')
        self.assertEqual(result[3], u'> The CPS Team.')

        result = replyToBody('Tarek Ziad� <tz@nuxeo.com>', body)
        result = HTMLize(result)

        result = result.split('<br/>')

        self.assertEqual(result[0], u'&gt; Tarek Ziad\xe9 wrote')
        self.assertEqual(result[1], u'&gt; Welcome to your cps webmail, webmailtest4 !')
        self.assertEqual(result[2], u'&gt; ')
        self.assertEqual(result[3], u'&gt; The CPS Team.')


    def test_sanitizeHTML(self):
        html = 'dfghjuik<body> ghfrtgy<script >hj</script>uikolm�</body>'
        res = sanitizeHTML(html)
        self.assertEquals(res, 'dfghjuik ghfrtgyhjuikolm\xf9')

        html = 'dfghjuik&lt;body&gt; ghfrtgy&lt;script &gt;hj&lt;/script&gt;uikolm�&lt;/body&gt;'
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

    def test_removeHTML2(self):
        html = 'ezezf<br><span>ezezf</span><br>'
        res = removeHTML(html)
        self.assertEquals(res, 'ezezf\r\nezezf\r\n')

    def test_removeHTML3(self):
        result = replyToBody('<tz@nuxeo.com>', '')

        self.assertEquals(result, u'> tz@nuxeo.com wrote\r\n> ')

    def oldtest_HTMLToTextNoEffect(self):
        html = """Welcome to your cps webmail, webmailtest4 !

The CPS Team.
"""
        res = removeHTML(html)
        self.assertEquals(res, """Welcome to your cps webmail, webmailtest4 !

The CPS Team.
""")

    def test_decodeHeader(self):
        # tests unicoding issues
        res = decodeHeader('Tarek Ziad� <webmailtest@nuxeo.com>')
        self.assertEquals(type(res), unicode)
        self.assertEquals(res, u'Tarek Ziad� <webmailtest@nuxeo.com>')

        # japanese encoding
        # XXX need to find better here
        res = decodeHeader('=?iso-2022-jp?Q?8=1B=24B=40iK=7C1=5F=24N3MF=40J=7D=1B=28B?= =?iso-2022-jp?Q?=1B=24BK!!=26=25a=25k=25=5E=25=2C=258=25s=1B=28B?= <delivery@hosyou-r01.mine.nu>')
        self.assertEquals(type(res), unicode)
        self.assertEquals(res, u'8\u5343\u4e07\u5186\u306e\u7372\u5f97\u65b9\u6cd5\u30fb\u30e1\u30eb\u30de\u30ac\u30b8\u30f3<delivery@hosyou-r01.mine.nu>')

    def test_getCurrentDateStr(self):
        date = getCurrentDateStr()


    def test_isValidEmail(self):
        self.assert_(isValidEmail('tz@nuxeo.com'))
        self.assert_(isValidEmail('tarek@nuxeo.comfmm'))
        self.assert_(not isValidEmail('tarek_AT_nuxeo.commm'))
        self.assert_(not isValidEmail('fezefz'))
        self.assert_(not isValidEmail(''))
        self.assert_(isValidEmail('tdddd.dddddd.ddd@nu.x.eo.com'))

    def test_parseDateStringWeirdCases(self):
        date = parseDateString('Sat, 04 Dec 2004 20:03:34 +0190')
        self.assertEquals(date, datetime(2004, 12, 4, 20, 3, 34))

        # sometime the last part is not ok,
        # those are hard to guess so we return 1 jan 70
        date = parseDateString('Sat, 04 Dec 2004 20:03:34 01900')
        self.assertEquals(date, datetime(1970, 1, 1, 0, 0))

    def test_asynCall(self):
        caller = AsyncCall(self.method, 1, 3)
        caller.start()
        # place to drink a coffe
        caller.join()
        self.assertEquals(self.total, 4)

    def test_asynCallTerminate(self):
        caller = AsyncCall(self.method, 1, 3)
        caller.onTerminate(self.addOne)
        caller.start()
        # place to drink a coffe
        caller.join()
        self.assertEquals(self.total, 5)

    def test_secureunicode(self):
        res = secureUnicode(u'����� � ��� ������� ������� ')
        self.assertEquals(res, u'����� � ��� ������� ������� ')

    def test_linkifyMailBody(self):
        body = 'ezlkhezl tz@nuxeo.com efzoihefzouh https://google.com zdfz'
        result = linkifyMailBody(body)
        res = 'ezlkhezl <a href="mailto:tz@nuxeo.com">tz@nuxeo.com</a> efzoihefzouh <a href="https://google.com" target="_blank">https://google.com</a> zdfz'

        self.assertEquals(result, res)

        body = ' ftygu tz@nuxeo.com uig'
        result = linkifyMailBody(body, r'<a href="http://xxx/sendmail?mail=\1">\1</a>')
        res = ' ftygu <a href="http://xxx/sendmail?mail=tz@nuxeo.com">tz@nuxeo.com</a> uig'
        self.assertEquals(result, res)

        # try with sticked tag
        body = ' <br>ftygu http://gyuhji</br>'
        result = linkifyMailBody(body, r'<a href="http://xxx/sendmail?mail=\1">\1</a>')
        res = ' <br>ftygu <a href="http://gyuhji" target="_blank">http://gyuhji</a></br>'
        self.assertEquals(result, res)

        body = 'http://nuxeo.com/<br>Nuxeo Collaborative Portal Server'
        res = '<a href="http://nuxeo.com/" target="_blank">http://nuxeo.com/</a><br>Nuxeo Collaborative Portal Server'
        result = linkifyMailBody(body)
        self.assertEquals(result, res)

    def test_answerSubject(self):

        res = answerSubject('Re: ytfuygiujoipok')
        self.assertEquals(res, 'Re: ytfuygiujoipok')
        res = answerSubject('ytfuygiujoipok')
        self.assertEquals(res, 'Re: ytfuygiujoipok')

        res = answerSubject('Re: ytfuygiujoipok', True)
        self.assertEquals(res, 'Fwd: Re: ytfuygiujoipok')
        res = answerSubject('ytfuygiujoipok', True)
        self.assertEquals(res, 'Fwd: ytfuygiujoipok')
        res = answerSubject('Fwd: ytfuygiujoipok', True)
        self.assertEquals(res, 'Fwd: ytfuygiujoipok')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UtilsTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.utils'),
        ))

