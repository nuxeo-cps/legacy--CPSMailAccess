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

from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase, _print

from zope.testing import doctest
from zope.publisher.browser import FileUpload

from rdflib.URIRef import URIRef

from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailmessageview import MailMessageView
from Products.CPSMailAccess.interfaces import IMailMessage
from Products.CPSMailAccess.mailmessageview import MailMessageView
from Products.CPSMailAccess.mailsearch import get_uri
from Products.CPSMailAccess.zemantic.query import Query
from Products.CPSMailAccess.tests import __file__ as landmark

from basetestcase import MailTestCase

class FakeFieldStorage:
    file = None
    filename = ''
    headers = []

def openfile(filename, mode='r'):
    path = os.path.join(os.path.dirname(landmark), 'data', filename)
    return open(path, mode)


class MailMessageViewTestCase(MailTestCase):


    def fakePhysicalPath(self):
        #
        return ('', 'http://ok/path')

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
            '<a href="/writeTo.html?msg_to=Barry%20%3Cbarry%40digicool.com%3E">Barry &lt;barry@digicool.com&gt;</a>')

        self.assertEquals(view.renderToList(),
            '<a href="/writeTo.html?msg_to=Dingus%20Lovers%20%3Ccravindogs%40cravindogs.com%3E">Dingus Lovers &lt;cravindogs@cravindogs.com&gt;</a>')

        ob = MailMessage()
        view = MailMessageView(ob, None)
        self.assertEquals(view.renderFromList(), u'')
        self.assertEquals(view.renderToList(), u'')

    def test_MailMessageparts(self):
        # testing message parts
        box = self._getMailBox()
        ob = self.getMailInstance(1)
        ob = ob.__of__(box)
        body = ob.getDirectBody()

        self.assertNotEquals(body, '')
        self.assertNotEquals(body, None)
        view = MailMessageView(ob, None)
        viewbody = view.renderBody()
        self.assertNotEquals(body.find('http://www.zzz.org/mailman/listinfo/ppp'), -1)

    def test_MailMessageViewMethods(self):
        ob = self.getMailInstance(6)
        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)
        """
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
        self.assertEquals(date, 'Sat 21/04/01 01:35')

    def test_attachedfiles(self):
        ob = self.getMailInstance(6)

        my_file3 = self._openfile('PyBanner048.gif')
        storage3 = FakeFieldStorage()
        storage3.file = my_file3
        storage3.filename = 'SecondPyBansxzner048.gif'
        uploaded3 = FileUpload(storage3)
        ob.getPhysicalPath = self.fakePhysicalPath

        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)
        ob.attachFile(uploaded3)

        files = view.attached_files()
        self.assertEquals(len(files), 1)
        self.assertEquals(len(files[0]), 1)
        file = files[0][0]
        self.assertEquals(file['mimetype'], 'image/gif')
        self.assertEquals(file['filename'], 'SecondPyBansxzner048.gif')

    def test_multipartAlternativeRead(self):
        # lotus note mail message
        # the body gets empty in the view
        # added this test
        box = self._getMailBox()
        ob = self.getMailInstance(35)
        ob = ob.__of__(box)

        ob.getPhysicalPath = self.fakePhysicalPath

        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)

        body = view._bodyRender(ob)
        body = body.split('<br/>')

        self.assertEquals(body[0], u'sqdsqd d')
        self.assertEquals(body[7], u'')

        body = view.renderBody()

        self.assertNotEquals(body, '')

    def test_renderBody(self):
        # thunderbird html
        box = self._getMailBox()
        ob = box._addMessage('msg', 'msg')


        ob.setDirectBody(u'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"> <html> <head>  <meta content="text/html;charset=ISO-8859-1" http-equiv="Content-Type">  <title></title> </head> <body bgcolor="#ffffff" text="#000000"> ezezf<br> ezf<br> <b>ezf</b><br> ef<br> <br> <u>ez<br> <br> <span class="moz-smiley-s6"><span> :-[ </span></span><br> </u>ezf<br> </body> </html>')

        ob.setHeader('Content-Type', 'text/html')
        ob.setHeader('Charset', 'ISO-8859-15')

        view = MailMessageView(ob, None)
        self.assert_(view)

        body = view.renderBody()
        self.assertEquals(body, u'         ezezf<br/> ezf<br/> <b>ezf</b><br/> ef<br/> <br/> ez<br/> <br/> <span class="moz-smiley-s6"><span> :-[ </span></span><br/> ezf<br/>  ')

    def test_renderHeaderList(self):
        # checks unicoding
        ob = self.getMailInstance(6)
        ob.setHeader('From', u'Tarek Ziadé')

        ob.getPhysicalPath = self.fakePhysicalPath

        # need to set up context and request object here
        view = MailMessageView(ob, None)

        hl = view.renderHeaderList('From')
        self.assertEquals(hl, u'Tarek Ziadé')

    def test_renderHeaderListWithNones(self):
        # checks unicoding
        ob = self.getMailInstance(6)
        ob.setHeader('From', None)

        ob.getPhysicalPath = self.fakePhysicalPath

        # need to set up context and request object here
        view = MailMessageView(ob, None)

        hl = view.renderHeaderList('From')
        self.assertEquals(hl, u'?')

    def test_reply_all(self):
        mbox =self._getMailBox()
        ob = self.getMailInstance(6)

        ob = ob.__of__(mbox)

        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)

        ob.addHeader('To', 'tarek')
        ob.addHeader('To', 'bob')
        ob.addHeader('Cc', 'bill')
        ob.addHeader('Cc', 'billie')

        # testing reply all
        view.reply_all()

        ed_msg = mbox.getCurrentEditorMessage()

        # we should get all 4 persons
        """
        ToList = ed_msg.getHeader('To')
        self.assert_('tarek' in ToList)
        self.assert_('bob' in ToList)
        self.assert_('bill' in ToList)
        self.assert_('billie' in ToList)
        """

    def test_reply(self):
        mbox =self._getMailBox()
        ob = self.getMailInstance(6)

        ob = ob.__of__(mbox)

        # need to set up context and request object here
        view = MailMessageView(ob, None)
        self.assert_(view)

        ob.addHeader('To', 'tarek')
        ob.addHeader('To', 'bob')
        ob.addHeader('Cc', 'bill')
        ob.addHeader('Cc', 'billie')

        # testing reply all
        view.reply()

        ed_msg = mbox.getCurrentEditorMessage()

        # we should get only the From person
        self.assertEquals(ed_msg.getHeader('To'), ob.getHeader('From'))

    def test_multipleTos(self):
        mbox = self._getMailBox()
        ob = self.getMailInstance(42)
        ob = ob.__of__(mbox)

        # need to set up context and request object here
        view = MailMessageView(ob, None)
        rendered_to = view.renderToList()
        self.assertEquals(len(rendered_to.split(',\n')), 3)

    def test_charmap_errors(self):
        mbox = self._getMailBox()
        for mail_index in (43, 44):
            ob = self.getMailInstance(mail_index)
            ob = ob.__of__(mbox)
            view = MailMessageView(ob, None)

            # will raise errors if not viewable in iso
            rendered_body = view.renderBody()
            string_ = rendered_body.encode('ISO-8859-15')

            rendered_subject = view.renderSubject()
            string_ = rendered_subject.encode('ISO-8859-15')

            render_from_list = view.renderFromList()
            string_ = render_from_list.encode('ISO-8859-15')

    def test_headerCount(self):
        mbox = self._getMailBox()
        ob = self.getMailInstance(43)
        ob = ob.__of__(mbox)
        view = MailMessageView(ob, None)
        Ccs = view.headerCount('Cc')
        self.assertEquals(Ccs, 0)

    def test_quotebraker(self):
        # quotes would brake linking
        mbox = self._getMailBox()
        ob = self.getMailInstance(43)
        ob.setHeader('From', '"Tarek" <tz@nuxeo.com>')
        view = MailMessageView(ob, None)
        res = view.renderFromList()
        self.assertEquals(res, u'<a href="/writeTo.html?msg_to=%22Tarek%22%20%3Ctz%40nuxeo.com%3E">"Tarek" &lt;tz@nuxeo.com&gt;</a>')

    def test_setThreadHeader(self):
        mbox = self._getMailBox()

        origin = self.getMailInstance(44)
        self.assertEquals(origin.getHeader('References'), [])
        origin.setHeader('References', '<Ref1>')

        message = self.getMailInstance(43)

        view = MailMessageView(message, None)

        view._setThreadHeader(message, origin)
        # now checks mail integrity
        msg = message.getRawMessage()

        refs = message.getHeader('References')

        self.assert_('<15893651.1105277510670.JavaMail.nobody@hr_01_rev_b>' in refs)
        self.assert_('<Ref1>' in refs)

    def test_notificationEmail(self):
        mbox = self._getMailBox()

        message = self.getMailInstance(43)
        view = MailMessageView(message, None)

        self.assertEquals(view.notificationEmail(), None)

        message = self.getMailInstance(48)
        view = MailMessageView(message, None)

        self.assertEquals(view.notificationEmail(), u'Tarek Ziadé<tziade@xxxx.xxx>')

    def test_notify(self):
        mbox = self._getMailBox()
        message = self.getMailInstance(48)
        message = message.__of__(mbox)
        view = MailMessageView(message, None)
        self.assertRaises(AttributeError, view.notify, 0)

    def test_getReferences(self):
        mbox = self._getMailBox()
        cat = mbox._getZemanticCatalog()
        message = self.getMailInstanceT(48)
        message.setHeader('message-id', '<1>')
        message = message.__of__(mbox)
        cat.indexMessage(message)

        message2 = self.getMailInstanceT(47)
        message2 = message2.__of__(mbox)
        message2.setHeader('message-id', '<2>')
        message2.setHeader('references', '<1>')
        self.assertEquals(message2.getHeader('references'), ['<1>'])
        cat.indexMessage(message2)

        # verify indexing
        uri = get_uri(message2)
        res = list(cat.query(Query(uri, u'<thread>', None)))
        self.assertEquals(len(res), 1)
        """
        view = MailMessageView(message2, None)
        self.assertRaises(AttributeError, view.notify, 0)
        refs = view.getReferences()
        self.assertEquals(refs, ['2'])
        """

    def test_forwardWithAttachedFile(self):
        # tests that messages forwarded does not loose their attached
        # parts
        mbox = self._getMailBox()

        # attach a file
        ob = self.getMailInstance(43)
        ob = ob.__of__(mbox)
        ob.getPhysicalPath = self.fakePhysicalPath

        my_file = self._openfile('PyBanner048.gif')
        storage = FakeFieldStorage()
        storage.file = my_file
        storage.filename = 'SecondPyBansxzner048.gif'
        uploaded = FileUpload(storage)
        ob.attachFile(uploaded)

        # forward the mail
        view = MailMessageView(ob, None)
        self.assert_(view)
        view.forward()

        # now verify the result in the editor
        msg = mbox._cache.query('maileditor')
        files = msg.getFileList()
        self.assertEquals(len(files), 1)
        file = files[0]
        self.assertEquals(file['filename'], 'SecondPyBansxzner048.gif')
        self.assertEquals(file['mimetype'], 'image/gif')

    def _getBoxMail(self):
        return 'bob'

    def test_prepareReplyRecipient(self):
        mbox = self._getMailBox()

        # attach a file
        ob = self.getMailInstance(43)
        ob = ob.__of__(mbox)
        ob.getPhysicalPath = self.fakePhysicalPath
        ob.addHeader('To', 'bob')
        ob.addHeader('Cc', 'bob')

        view = MailMessageView(ob, None)
        self.assert_(view)
        view._getBoxMail = self._getBoxMail

        view.prepareReplyRecipient(reply_all=1)

    def test_renderLinkedHeaderList(self):
        mbox = self._getMailBox()
        ob = self.getMailInstance(50)
        ob = ob.__of__(mbox)
        ob.getPhysicalPath = self.fakePhysicalPath
        view = MailMessageView(ob, None)
        rendered = view._renderLinkedHeaderList('Cc')
        self.assertEquals(rendered, u'')

    def test_headerCountWithEmptyField(self):
        mbox = self._getMailBox()
        ob = self.getMailInstance(50)
        ob = ob.__of__(mbox)
        ob.getPhysicalPath = self.fakePhysicalPath
        view = MailMessageView(ob, None)
        self.assertEquals(view.headerCount('Cc'), 0)

    def test_removeNone(self):
        view = MailMessageView(None, None)
        self.assert_(not view._removeNone(None))
        self.assert_(not view._removeNone(''))
        self.assert_(not view._removeNone(['           ']))
        self.assert_(not view._removeNone(['']))
        self.assert_(not view._removeNone(['           ', '']))
        self.assert_(view._removeNone(['not_me']))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessageview'),
        ))
