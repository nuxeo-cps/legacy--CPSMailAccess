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

from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailmessageview import MailMessageView
from Products.CPSMailAccess.interfaces import IMailMessage
from Products.CPSMailAccess.mailmessageview import MailMessageView
from Products.CPSMailAccess.tests import __file__ as landmark

from basetestcase import MailTestCase

class FakeFieldStorage:
    file = None
    filename = ''
    headers = []

installProduct('TextIndexNG2')

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
            '<a href="/writeTo.html?msg_to=Barry <barry@digicool.com>">Barry &lt;barry@digicool.com&gt;</a>')

        self.assertEquals(view.renderToList(),
            '<a href="/writeTo.html?msg_to=Dingus Lovers <cravindogs@cravindogs.com>">Dingus Lovers &lt;cravindogs@cravindogs.com&gt;</a>')

        ob = MailMessage()
        view = MailMessageView(ob, None)
        self.assertEquals(view.renderFromList(),
                          u'<a href="/writeTo.html?msg_to=?">?</a>')
        self.assertEquals(view.renderToList(),
                          u'<a href="/writeTo.html?msg_to=?">?</a>')

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
        self.assertEquals(date, 'Fri 20/04/01 19:35')

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
        self.assertEquals(body, u"sqdsqd d<br/>sqdsqd<br/>qsd<br/>sd<br/>qs<br/>dsqdqsdsq<br/><br/><br/>_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _<br/><br/>Mme XXX<br/>Direction Informatique<br/>xxxx - SIEGE<br/>Tel : XXX<br/>_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _<br/><br/>--------------------------------------------<br/><br/>Ce mail est \xe0 l'attention exclusive des destinataires d\xe9sign\xe9s. Il peut<br/>contenir des informations confidentielles. Si vous le recevez par erreur,<br/>merci de le d\xe9truire et d'en informer sans d\xe9lais l'exp\xe9diteur.<br/><br/>Le contenu de ce mail ne pourrait engager la responsabilit\xe9 de la Banque<br/>Centrale des Etats de l'Afrique de l'Ouest que s'il a \xe9t\xe9 \xe9mis par une<br/>personne d\xfbment habilit\xe9e, agissant dans le cadre strict des fonctions<br/>auxquelles elle est employ\xe9e et \xe0 des fins non \xe9trang\xe8res \xe0 ses attributions.<br/><br/>Toute diffusion, copie, publication partielle ou totale, ou toute autre<br/>utilisation est interdite, sauf autorisation.<br/><br/>--------------------------------------------<br/><br/>")

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
        self.assertEquals(body, u'         ezezf<br> ezf<br> <b>ezf</b><br> ef<br> <br> ez<br> <br> <span class="moz-smiley-s6"><span> :-[ </span></span><br> ezf<br>  ')

    def test_renderHeaderList(self):
        # checks unicoding
        ob = self.getMailInstance(6)
        ob.setHeader('From', u'Tarek Ziadé')

        ob.getPhysicalPath = self.fakePhysicalPath

        # need to set up context and request object here
        view = MailMessageView(ob, None)

        hl = view.renderHeaderList('From')
        self.assertEquals(hl, u'Tarek Ziadé')

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
        self.assertEquals(len(rendered_to.split(',\n')), 5)

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


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageViewTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessageview'),
        ))
