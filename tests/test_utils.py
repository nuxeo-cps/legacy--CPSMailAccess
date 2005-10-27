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
#
# $Id$

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

        body = 'voici\r\nun petit mesééééééésage'
        from_ = 'mé'
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
        result = replyToBody('Tarek Ziadé <tz@nuxeo.com>', body)

        result = result.split('\r\n')

        self.assertEqual(result[0], u'> Tarek Ziad\xe9 wrote')
        self.assertEqual(result[1], u'> Welcome to your cps webmail, webmailtest4 !')
        self.assertEqual(result[2], u'> ')
        self.assertEqual(result[3], u'> The CPS Team.')

        result = replyToBody('Tarek Ziadé <tz@nuxeo.com>', body)
        result = HTMLize(result)

        result = result.split('<br/>')

        self.assertEqual(result[0], u'&gt; Tarek Ziad\xe9 wrote')
        self.assertEqual(result[1], u'&gt; Welcome to your cps webmail, webmailtest4 !')
        self.assertEqual(result[2], u'&gt; ')
        self.assertEqual(result[3], u'&gt; The CPS Team.')


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
        res = decodeHeader('Tarek Ziadé <webmailtest@nuxeo.com>')
        self.assertEquals(type(res), unicode)
        self.assertEquals(res, u'Tarek Ziadé <webmailtest@nuxeo.com>')

        # japanese encoding
        # XXX need to find better here
        res = decodeHeader('=?iso-2022-jp?Q?8=1B=24B=40iK=7C1=5F=24N3MF=40J=7D=1B=28B?= =?iso-2022-jp?Q?=1B=24BK!!=26=25a=25k=25=5E=25=2C=258=25s=1B=28B?= <delivery@hosyou-r01.mine.nu>')
        self.assertEquals(type(res), unicode)
        self.assertEquals(res.find('?iso-2022-jp?'), -1)

    def test_decodeHeader2(self):
        res = decodeHeader('=?ISO-8859-1?B?UmU6IGFsZXJ0ZSBzZWN1cml06SBPT28?=')
        # XXX unable to decode it... :/
        self.assertEquals(res, '=?ISO-8859-1?B?UmU6IGFsZXJ0ZSBzZWN1cml06SBPT28?=')


    def test_isValidEmail(self):
        self.assert_(isValidEmail('tz@nuxeo.com'))
        self.assert_(isValidEmail('tarek@nuxeo.comfmm'))
        self.assert_(not isValidEmail('tarek_AT_nuxeo.commm'))
        self.assert_(not isValidEmail('fezefz'))
        self.assert_(not isValidEmail(''))
        self.assert_(isValidEmail('gracinet@nuxeo-tests.com'))
        self.assert_(isValidEmail('tdddd.dddddd.ddd@nu.x.eo.com'))

    def test_parseDateStringWeirdCases(self):
        date = parseDateString('Sat, 04 Dec 2004 20:03:34 +0190')
        self.assertEquals(date, datetime(2004, 12, 4, 18, 33, 34))

        # sometime the last part is not ok,
        # those are hard to guess so we return 1 jan 70
        date = parseDateString('Sat, 04 Dec 2004 20:03:34 01900')
        self.assertEquals(date, datetime(2004, 12, 4, 2, 3, 34))

        date = parseDateString('Mon 04/04/05 13:29')
        self.assertEquals(date, datetime(2005, 4, 4, 13, 29, 0))

    def FIXMEtest_localizeDateString(self):
        self.assertEquals(localizeDateString('Sat, 04 Dec 2004'),
                          'Sat 04/12/04 00:00')

        self.assertEquals(localizeDateString('Sat, 04 Dec 2004', lang='fr'),
                          'Sam 04/12/04 00:00')


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
        res = secureUnicode(u'ëèäåð â Óåá Õîñòèíã ðåøåíèÿ ')
        self.assertEquals(res, u'ëèäåð â Óåá Õîñòèíã ðåøåíèÿ ')

    def test_linkifyMailBody(self):
        body = 'ezlkhezl tz@nuxeo.com efzoihefzouh https://google.com zdfz'
        result = linkifyMailBody(body)
        res = 'ezlkhezl <a href="mailto:tz@nuxeo.com">tz@nuxeo.com</a> efzoihefzouh <a href="https://google.com" target="_blank">https://google.com</a> zdfz'

        self.assertEquals(result, res)

        body = ' ftygu tz@nuxeo.com uig'
        result = linkifyMailBody(body, r'<a href="http://xxx/sendmail?mail=\3">\3</a>')
        res = ' ftygu <a href="http://xxx/sendmail?mail=tz@nuxeo.com">tz@nuxeo.com</a> uig'
        self.assertEquals(result, res)

        # try with sticked tag
        body = ' <br>ftygu http://gyuhji</br>'
        result = linkifyMailBody(body, r'<a href="http://xxx/sendmail?mail=\3">\3</a>')
        res = ' <br>ftygu <a href="http://gyuhji" target="_blank">http://gyuhji</a></br>'
        self.assertEquals(result, res)

        body = 'http://nuxeo.com/<br>Nuxeo Collaborative Portal Server'
        res = ('<a href="http://nuxeo.com/" target="_blank">http://nuxeo.com/</a><br>Nu'
               'xeo Collaborative Portal Server')
        result = linkifyMailBody(body)
        self.assertEquals(result, res)

        mail_body = """
        http://www.nuxeo.com
        --
        Tarek Ziadé | Nuxeo R&D (Paris, France)
        CPS Plateform : http://www.cps-project.org
        mail: tziade@nuxeo.com | tel: +33 (0) 6 30 37 02 63
        You need Zope 3 - http://www.z3lab.org/
        """

        result = linkifyMailBody(mail_body)
        wanted_result = """
        <a href="http://www.nuxeo.com" target="_blank">http://www.nuxeo.com</a>
        --
        Tarek Ziadé | Nuxeo R&D (Paris, France)
        CPS Plateform : <a href="http://www.cps-project.org" target="_blank">http://www.cps-project.org</a>
        mail: <a href="mailto:tziade@nuxeo.com">tziade@nuxeo.com</a> | tel: +33 (0) 6 30 37 02 63
        You need Zope 3 - <a href="http://www.z3lab.org/" target="_blank">http://www.z3lab.org/</a>
        """

        result = linkifyMailBody("""
        <http://www.nuxeo.com>
        """)
        self.assertEquals(result, """
        <a href="http://www.nuxeo.com" target="_blank">http://www.nuxeo.com</a>
        """)

        mail_body = """
        <http://www.nuxeo.com>
        --
        Tarek Ziadé | Nuxeo R&D (Paris, France)
        CPS Plateform : <http://www.cps-project.org>
        mail: <tziade@nuxeo.com> | tel: +33 (0) 6 30 37 02 63
        You need Zope 3 - <http://www.z3lab.org/>
        """
        result = linkifyMailBody(mail_body)
        wanted_result = """
        <a href="http://www.nuxeo.com" target="_blank">http://www.nuxeo.com</a>
        --
        Tarek Ziadé | Nuxeo R&D (Paris, France)
        CPS Plateform : <a href="http://www.cps-project.org" target="_blank">http://www.cps-project.org</a>
        mail: <a href="mailto:tziade@nuxeo.com">tziade@nuxeo.com</a> | tel: +33 (0) 6 30 37 02 63
        You need Zope 3 - <a href="http://www.z3lab.org/" target="_blank">http://www.z3lab.org/</a>
        """

        self.assertEquals(result, wanted_result)


        result = linkifyMailBody("""
        <http://www.nuxeo.com>,
        """)
        self.assertEquals(result, """
        <a href="http://www.nuxeo.com" target="_blank">http://www.nuxeo.com</a>,
        """)

        mail_body = ('Boîtier <http://www.grosbill.com/fr/informatique/boitier-'
                     'pc/liste.html>, *Carte graphique*')

        result = linkifyMailBody(mail_body)
        wanted_result = ('Boîtier <a href="http://www.grosbill.com/fr/informati'
                         'que/boitier-pc/liste.html" target="_blank">http://www'
                         '.grosbill.com/fr/informatique/boitier-pc/liste.html</a'
                         '>, *Carte graphique*')

        self.assertEquals(result, wanted_result)

        result = linkifyMailBody('<img src="cid:some@source"/>')
        self.assertEquals(result, '<img src="cid:some@source"/>')

        result = linkifyMailBody('http://some@source')
        self.assertEquals(result, '<a href="http://some@source" target="_blank">http://some@source</a>')


        result = linkifyMailBody('http://so:me@sou:rce')
        self.assertEquals(result, '<a href="http://so:me@sou:rce" target="_blank">http://so:me@sou:rce</a>')

        result = linkifyMailBody('http://so:me@sou:rce http://so:me@sou:rce')
        self.assertEquals(result, ('<a href="http://so:me@sou:rce" target="_blank">http://so:me@sou:rce</a> '
                                   '<a href="http://so:me@sou:rce" target="_blank">http://so:me@sou:rce</a>'))


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

    def test_Utf8ToIso(self):
        res = Utf8ToIso('Ã©Ã©')
        self.assertEquals(res, 'éé')

    def test_createDigest(self):
        msg = self.getMailInstance(2)
        self.assertEquals(createDigest(msg), 'ea879bcd72364153266cdd7d2c59c2d4')
        list_ = {'From': 'okokok', '2': 'opoihuou'}
        md5 = createDigestFromList(list_)
        self.assertEquals(md5,'015cded315e5d0f1e5f7ff295f09f306')

    def test_translate(self):
        # make sure it works if Localizer is not there
        ob = self
        res = translate(ob, 'ok')
        self.assertEquals(res, 'ok')

    def test_referencesReader(self):
        ob = self.getMailInstance(49)
        refs = ob.getHeader('References')
        refs = parseRefs(refs[0])
        self.assertEquals(refs, ['<D3FB7D99-584E-48E2-9D62-30ED005E1452@nuxeo.com>',
                                 '<42A87078.2060601@nuxeo.com>',
                                 '<4D23F833-EB8A-42DF-BB1D-4ADED7203590@nuxeo.com>'])

        refs = parseRefs('<42A87078.2060601@nuxeo.com>')
        self.assertEquals(refs, ['<42A87078.2060601@nuxeo.com>'])

    def test_shrinkHtml(self):
        text = 'Joe wrote:\n> ezc\n  > cez\n> dezez\n > errv\n\nHello\n\nWorld\n'
        text = shrinkHtml(text)
        self.assertEquals(text, '<span class="shrinkable not_hidden_part">Joe wrote:<br/></span><span class="shrinkable not_hidden_part">> ezc<br/></span><span class="shrinkable not_hidden_part">  > cez<br/></span><span class="shrinkable not_hidden_part">> dezez<br/></span><span class="shrinkable not_hidden_part"> > errv<br/></span><br/>Hello<br/><br/>World<br/><span class="shrinkable not_hidden_part"><br/></span>')


    def test_divideMailBody(self):
        self.assertEquals(divideMailBody('\nhoih\n<br/>oug'),
                          '<br/>hoih<br/><br/>oug')

        mail_content = """
> Untel wrote:
> ok
> ok ok

ok then"""

        mail_repr = '<br/><div class="bloc_0"><div class="topicRetractor" onmouseover="setCursor(this)" onclick="toggleElementVisibility(\'topicBloc01\')"><img src="cpsma_retract_topic.png"/></div><div id="topicBloc01"> Untel wrote:<br/> ok<br/> ok ok</div></div><br/>ok then'

        self.assertEquals(divideMailBody(mail_content), mail_repr)

        mail_content = """
> Untel wrote:
> ok
>> sur ?
>> oui
> ok ok

ok then"""

        mail_repr = '<br/><div class="bloc_0"><div class="topicRetractor" onmouseover="setCursor(this)" onclick="toggleElementVisibility(\'topicBloc01\')"><img src="cpsma_retract_topic.png"/></div><div id="topicBloc01"> Untel wrote:<br/> ok<br/><div class="bloc_1"><div id="topicBloc12"> sur ?<br/> oui</div></div></div></div><br/>ok then'

        self.assertEquals(divideMailBody(mail_content), mail_repr)

    def test_getAuthenticatedMember(self):
        class FakeMemberShip:
            def getAuthenticatedMember(self):
                return None

        self.portal.portal_membership = FakeMemberShip()
        self.assertEquals(getAuthenticatedMember(self.portal), None)

    def test_getHumanReadableSize(self):
        self.assertEquals((-1, ''), getHumanReadableSize(''))
        self.assertEquals((300, 'o'), getHumanReadableSize(300))
        self.assertEquals((2, 'ko'), getHumanReadableSize(3000))
        self.assertEquals((-1, ''), getHumanReadableSize(None))
        self.assertEquals((183, 'o'), getHumanReadableSize('183'))

    def test_mimetype_to_icon_name(self):
        # if the icon does not exists, unknown.png is returned
        self.assertEquals('unknown.png', mimetype_to_icon_name('logbkjv'))
        self.assertEquals('application_pdf.png',
                          mimetype_to_icon_name('application/pdf'))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UtilsTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.utils'),
        ))

