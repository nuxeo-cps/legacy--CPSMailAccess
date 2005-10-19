#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
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
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase
import os, sys
from Products.CPSMailAccess.connectionlist import ConnectionList
import fakeimaplib
if sys.modules.has_key('imaplib'):
    del sys.modules['imaplib']
sys.modules['imaplib'] = fakeimaplib

from Products.CPSMailAccess.imapconnection import makeMailObject, IMAPConnection
from time import time,sleep
from basetestcase import MailTestCase

fake_imap_enabled  = 1


"""
    xxxx
    need to finish fake IMAP lib
"""
class IMAPConnectionTestCase(MailTestCase):

    old_uimaplib = None

    def makeConnection(self):
        my_params = {}
        my_params['HOST'] = 'localhost'
        my_params['UserID'] = 'tarek'
        my_params['UserPassword'] = 'tarek'
        my_params['TYPE'] = 'IMAP'
        myconnection = makeMailObject(my_params)
        return myconnection

    def test_Instance(self):
        # testing simple instanciation with parameters
        if not fake_imap_enabled:
            return
        my_params = {}
        my_params['HOST'] = 'localhost'
        my_params['UserID'] = 'tarek'
        my_params['UserPassword'] = 'tarek'
        my_params['TYPE'] = 'IMAP'

        # regular connection
        myconnection = IMAPConnection(my_params)

        self.assertNotEqual(myconnection, None)

    def test_SSLInstance(self):
        # testing simple SSL instanciation with parameters
        if not fake_imap_enabled:
            return
        my_params = {}
        my_params['HOST'] = 'localhost'
        my_params['UserID'] = 'tarek'
        my_params['UserPassword'] = 'tarek'
        my_params['TYPE'] = 'IMAP'
        my_params['SSL'] = 1

        # regular connection
        myconnection = IMAPConnection(my_params)

        self.assertNotEqual(myconnection, None)

    def test_ConnectionParamsError(self):
        # testing simple instanciation with missing parameters
        from Products.CPSMailAccess.baseconnection import ConnectionParamsError
        my_params = {}

        self.failUnlessRaises(ConnectionParamsError, IMAPConnection, my_params)

    def test_login(self):
        # testing simple instanciation with missing parameters
        ob = self.makeConnection()
        login_result = ob.login('tarek','tarek')
        self.assertEquals(login_result, True)

    def test_partQueriedList(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        res = ob.partQueriedList('(FLAGS RFC822.SIZE RFC822.HEADER)')
        self.assertEquals(res, ['FLAGS', 'RFC822.SIZE', 'RFC822.HEADER'])

        res = ob.partQueriedList('(')
        self.assertEquals(res, [])

    def test_extractresults(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        fullquery = '(FLAGS RFC822.SIZE RFC822.HEADER)'

        res = ob._extractResult('FLAGS',
        ['1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'])
        self.assertEquals(res, ['Seen'])

        res = ob._extractResult('RFC822.SIZE', [('1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'), ')'])
        self.assertEquals(res, '515')

        res = ob._extractResult('RFC822.HEADER', ['1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'])

        self.assertEquals(res, [('Return-Path', '<webmaster@zopeur.org>'), ('Delivered-To', 'webmaster@openconference.org'), ('Received', '(qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000'), ('Message-ID', '<20050101013152.24339.qmail@ns2641.ovh.net>'), ('From', 'webmaster@openconference.org'), ('To', 'webmaster@openconference.org'), ('Subject', 'webmaster@openconference.org'), ('Date', 'Sat, 01 Jan 2005 02:31:52 +0100'), ('Mime-Version', '1.0'), ('Content-Type', 'text/plain; format=flowed; charset="iso-8859-1"'), ('Content-Transfer-Encoding', '8bit')])

        res = ob._extractResult('BODY',
                                ['1 (BODY ("text" "plain" NIL NIL NIL "8bit" 15 1))'])

        self.assertEquals(res,['text', 'plain', None, None, None, '8bit', 15, 1])

    def test_bodyExtraction(self):
        box = self._getMailBox()
        ob = self.makeConnection()

        fullquery = '(BODY)'

        res = ob._extractResult('BODY', ['2 (BODY ((("text" "plain" ("charset" "us-ascii") NIL NIL "8bit" 738 18)("text" "html" ("charset" "us-ascii") NIL NIL "8bit" 0 0) "alternative")("image" "jpeg" ("name" "wlogo.jpg") NIL NIL "base64" 7226) "mixed"))'])

        self.assertEquals(res, ['mixed', ['alternative',
                               ['text', 'plain', None, None, '8bit', 738, 18,
                               ['charset', 'us-ascii']], ['text', 'html', None,
                                None, '8bit', 0, 0, ['charset', 'us-ascii']]],
                               ['image', 'jpeg', None, None, 'base64', 7226,
                               ['name', 'wlogo.jpg']]])


        res = ob._extractResult('BODY', '(BODY ("text" "plain" NIL NIL NIL "8bit" 1997 35))')
        self.assertEquals(res, ['text', 'plain', None, None, None, '8bit', 1997, 35])

    def test_bodyPEEK(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        fullquery = '(BODY.PEEK[1])'

        res = ob._extractResult('BODY.PEEK[1]', [('1 (BODY[1] {550}', " \r\n.../...\r\n\r\n> CPS, es-tu l\xe0... :)\r\n\r\nIl \xe9tait l\xe0 o\xf9 on ne l'attendait pas forc\xe9ment...\r\n;o)\r\n\r\nJo\xebl Kermabon\r\nNeptune Internet Services\r\n\r\nLe Jeudi 17 F\xe9vrier 2005 16:07, Damien Wyart avait \xe9crit :\r\n> * Joel Kermabon <J.Kermabon@neptune.fr> [170205 15:56]:\r\n> > Une conscience externe s'est manifest\xe9e avec efficacit\xe9...\r\n>\r\n> CPS, es-tu l\xe0... :)\r\n\r\n_______________________________________________\r\ncps-users-fr \r\nAdresse de la liste : cps-users-fr@lists.nuxeo.com\r\nGestion de l'abonnement : <http://lists.nuxeo.com/mailman/listinfo/cps-users-fr>\r\n"), ')'])

        self.assertEquals(res," \r\n.../...\r\n\r\n> CPS, es-tu l\xe0... :)\r\n\r\nIl \xe9tait l\xe0 o\xf9 on ne l'attendait pas forc\xe9ment...\r\n;o)\r\n\r\nJo\xebl Kermabon\r\nNeptune Internet Services\r\n\r\nLe Jeudi 17 F\xe9vrier 2005 16:07, Damien Wyart avait \xe9crit :\r\n> * Joel Kermabon <J.Kermabon@neptune.fr> [170205 15:56]:\r\n> > Une conscience externe s'est manifest\xe9e avec efficacit\xe9...\r\n>\r\n> CPS, es-tu l\xe0... :)\r\n\r\n_______________________________________________\r\ncps-users-fr \r\nAdresse de la liste : cps-users-fr@lists.nuxeo.com\r\nGestion de l'abonnement : <http://lists.nuxeo.com/mailman/listinfo/cps-users-fr>\r\n"    )


    def test_parseIMAPMessage(self):

        box = self._getMailBox()
        ob = self.makeConnection()

        res = ob._parseIMAPMessage('"ok" ("sub1" "us-ascii")  ("sub2" "us-ascii")')
        self.assertEquals(res, ['ok', ['sub1', 'us-ascii'], ['sub2', 'us-ascii']])

        res = ob._parseIMAPMessage('"text" "plain" "8bit" 738 18')
        self.assertEquals(res, ['text', 'plain', '8bit', 738, 18])

        res = ob._parseIMAPMessage('"text" "plain" ("charset" "us-ascii") NIL NIL "8bit" 738 18')
        self.assertEquals(res, ['text', 'plain', None, None, '8bit', 738, 18, ['charset', 'us-ascii']])

        res = ob._parseIMAPMessage('("text" "plain" ("charset" "us-ascii") NIL NIL "8bit" 738 18)')
        self.assertEquals(res, [['text', 'plain', None, None, '8bit', 738, 18, ['charset', 'us-ascii']]])

        res = ob._parseIMAPMessage('((("text" "plain" ("charset" "us-ascii") NIL NIL "8bit" 738 18)("text" "html" ("charset" "us-ascii") NIL NIL "8bit" 0 0) "alternative")("image" "jpeg" ("name" "wlogo.jpg") NIL NIL "base64" 7226) "mixed")')

        self.assertEquals(res, [['mixed', ['alternative', ['text', 'plain', None, None, '8bit', 738, 18, ['charset', 'us-ascii']], ['text', 'html', None, None, '8bit', 0, 0, ['charset', 'us-ascii']]], ['image', 'jpeg', None, None, 'base64', 7226, ['name', 'wlogo.jpg']]]])


        res = ob._parseIMAPMessage('(BODY ((("text" "plain" ("charset" "us-ascii") NIL NIL "8bit" 738 18)("text" "html" ("charset" "us-ascii") NIL NIL "8bit" 0 0) "alternative")("image" "jpeg" ("name" "wlogo.jpg") NIL NIL "base64" 7226) "mixed"))')

        self.assertEquals(res, [['body', ['mixed', ['alternative', ['text', 'plain', None, None, '8bit', 738, 18, ['charset', 'us-ascii']], ['text', 'html', None, None, '8bit', 0, 0, ['charset', 'us-ascii']]], ['image', 'jpeg', None, None, 'base64', 7226, ['name', 'wlogo.jpg']]]]])


        res = ob._parseIMAPMessage('BODY ((("text" "plain" ("charset" "us-ascii") NIL NIL "8bit" 738 18)("text" "html" ("charset" "us-ascii") NIL NIL "8bit" 0 0) "alternative")("image" "jpeg" ("name" "wlogo.jpg") NIL NIL "base64" 7226) "mixed")')

        self.assertEquals(res, ['body', ['mixed', ['alternative', ['text', 'plain', None, None, '8bit', 738, 18, ['charset', 'us-ascii']], ['text', 'html', None, None, '8bit', 0, 0, ['charset', 'us-ascii']]], ['image', 'jpeg', None, None, 'base64', 7226, ['name', 'wlogo.jpg']]]])


    def test_infoExtraction(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        results = ob.fetch(box, 1, '(FLAGS RFC822.SIZE RFC822.HEADER)')
        self.assertEquals(results[0], ['Seen'])
        self.assertEquals(results[1], '515')

    def test_extractInfos(self):
        infos = ['related', ['alternative', ['text', 'plain', None, None,
          'quoted-printable', 3949, 104, ['charset', 'utf-8']], ['text', 'html',
          None, None, 'quoted-printable', 29240, 582, ['charset', 'utf-8']]],
           ['image', 'jpeg',
         '<004d01c4c8c5$4a5c6c20$6a012515@mairiedijon.org>', None,
         'base64', 30732, ['name', 'clip_image002.jpg']], ['image', 'jpeg',
          '<004e01c4c8c5$4a5c6c20$6a012515@mairiedijon.org>', None,
         'base64', 14904, ['name', 'clip_image004.jpg']]]

        box = self._getMailBox()
        ob = self.makeConnection()

        results = ob._extractInfos(infos, 1)
        self.assertEquals(results, ['alternative', ['text', 'plain', None, None,
          'quoted-printable', 3949, 104, ['charset', 'utf-8']], ['text', 'html',
          None, None, 'quoted-printable', 29240, 582, ['charset', 'utf-8']]])

        infos = ['text', 'plain', None, None, None, '8bit', 92, 6]
        results = ob._extractInfos(infos, 1)
        self.assertEquals(infos, results)

        infos = ['text', 'plain', None, None, '7bit', 841, 28, ['charset', 'us-ascii']]
        results = ob._extractInfos(infos, 1)
        self.assertEquals(infos, results)


        infos = ['related', ['text', 'html', None, None, '7bit', 384, 1,
         ['charset', 'us-ascii']], ['image', 'gif', '', None, 'base64', 15632,
          ['name', 'perpetual.gif']]]
        results = ob._extractInfos(infos, 2)
        self.assertEquals(results, ['image', 'gif', '', None,
         'base64', 15632, ['name', 'perpetual.gif']])


        infos = ['related', ['text', 'html', None, None, '7bit', 384, 1,
          ['charset', 'us-ascii']], ['image', 'gif',
           '<part1.08020703.07060906@vptfod@yahoo.com>', None, 'base64',
           15632, ['name', 'perpetual.gif']]]

        results = ob._extractInfos(infos, 1)
        self.assertEquals(results, ['text', 'html', None, None, '7bit', 384, 1,
          ['charset', 'us-ascii']])

        results = ob._extractInfos(infos, 2)
        self.assertEquals(results, ['image', 'gif',
           '<part1.08020703.07060906@vptfod@yahoo.com>', None, 'base64',
           15632, ['name', 'perpetual.gif']])

    def test_findClosingParenthesis(self):
        box = self._getMailBox()
        ob = self.makeConnection()
        text = 'f(uiguoig)czdcz'
        res = ob._findClosingParenthesis(text, 1)
        self.assertEquals(res, 9)
        self.assertEquals(text[2:9], 'uiguoig')

        text = 'f(ui(uoihuoiih(jhhghg(ohouh)  )guo)ig)czdcz'
        res = ob._findClosingParenthesis(text, 1)
        self.assertEquals(res, 37)
        self.assertEquals(text[2:37], 'ui(uoihuoiih(jhhghg(ohouh)  )guo)ig')

    def test_extractCommands(self):
        box = self._getMailBox()
        ob = self.makeConnection()

        headers = 'From To Cc Subject Date Message-ID In-Reply-To Content-Type'
        commands = '(FLAGS RFC822.SIZE BODY.PEEK[HEADER.FIELDS(%s)])' % headers

        extracted_commands = ob._extractCommands(commands)
        self.assertEquals(extracted_commands, ['FLAGS', 'RFC822.SIZE',
                                               'BODY.PEEK[HEADER.FIELDS(%s)]'
                                                % headers])

    def test_selectMailBox(self):
        ob = self.makeConnection()
        self.assertEquals(ob._getLastSelect(), None)
        ob._selectMailBox('FOO')
        self.assertEquals(ob._getLastSelect(), 'FOO')
        ob._selectMailBox('BAR')
        self.assertEquals(ob._getLastSelect(), 'BAR')

    def test_parseImapMessage2(self):
        # testing file names with spaces and quotes
        box = self._getMailBox()
        ob = self.makeConnection()
        parse = 'BODY (("text" "plain" ("charset" "iso-8859-15") NIL NIL "7bit" 206 7)("unknown" "" ("name" "piece =?x-unknown?Q?attach=E9e.txt?=") NIL NIL "base64"12) "mixed")'
        res = ob._parseIMAPMessage(parse)
        self.assertEquals(res, ['body', ['mixed', ['text', 'plain', None, None, '7bit', 206, 7, ['charset', 'iso-8859-15']], ['unknown', '', None, None, '"base64"12', ['name', 'piece =?x-unknown?q?attach=e9e.txt?=']]]])


    def test_extractResult2(self):
        ob = self.makeConnection()

        raw_imap = '(BODY (("text" "plain" NIL NIL "Notification" "8bit" 505 14)("message" "delivery-status" NIL NIL "Delivery report" "8bit" 369)("message" "rfc822" NIL NIL "Undelivered Message" "8bit" 101221 ("Fri, 09 Sep 2005 06:45:29 -0000" "test retour" (("basicuser" NIL "xxxx1" "xxxx.com")) (("basicuser" NIL "xxxx1" "xxxx.com")) (("basicuser" NIL "xxxx1" "xxxx.com")) ((NIL NIL "inexistant.sdflk" "free.fr")) NIL NIL NIL "<71803504.71803504>") (("text" "plain" ("charset" "iso-8859-15") NIL NIL "7bit" 38 3)("image" "jpeg" ("name" "a broken moment - hommage a la folie pure....1.0.jpg") NIL NIL "base64" 100352) "mixed") 28) "report"))'

        extracted = ob._extractResult('BODY', raw_imap)

        waited = ['report', ['text', 'plain', None, None, 'notification', '8bit', 505, 14], ['message', 'delivery-status', None, None, 'delivery report', '8bit', 369], ['message', 'rfc822', None, None, 'undelivered message', '8bit', 101221, 28, ['fri, 09 sep 2005 06:45:29 -0000', 'test retour', None, None, None, '<71803504.71803504>', [['basicuser', None, 'xxxx1', 'xxxx.com']], [[None, None, 'inexistant.sdflk', 'free.fr']]], ['mixed', ['text', 'plain', None, None, '7bit', 38, 3, ['charset','iso-8859-15']], ['image', 'jpeg', None, None, 'base64', 100352, ['name', 'a broken moment - hommage a la folie pure....1.0.jpg']]]]]

        self.assertEquals(extracted, waited)

    def test_getState(self):
        ob = self.makeConnection()
        state = ob.getState()
        self.assertEquals(state, 'NOAUTH')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(IMAPConnectionTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.imapconnection'),
        ))
