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
import unittest, os
from time import sleep
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct, ZopeTestCase

from Products.CPSMailAccess import smtpmailer
from Products.CPSMailAccess.smtpmailer import MailSender, \
                                              setMailElement, SmtpMailer, mail_sender
from Products.CPSMailAccess.tests import __file__ as landmark
from Products.CPSMailAccess.mailmessage import MailMessage

from basetestcase import MailTestCase

maildir_path = os.path.join(os.path.dirname(landmark), 'maildir')

class FakeMailer:
    def send(self, fromaddr, toaddrs, message):
        pass

class SMTPMailerTestCase(MailTestCase):

    def _cleanMaildir(self):
        """ cleans previous tests """
        os.popen('rm -rf %s' % maildir_path)

    def test_MailWriter(self):
        self._cleanMaildir()

        writer = SmtpMailer(maildir_path, direct_smtp=0)

        # writing a message into the maildir
        msg = self.getMailInstance(7)
        msg = msg.getRawMessage()
        writer._write('tarek', 'bill', msg, 'cool.smtp.com', 26, 'tarek',
                      'secret')

        # verify that is has been written in the maildir
        tmp_folder = os.path.join(maildir_path, 'new')
        files = list(os.walk(tmp_folder))[0][2]
        self.assertEquals(len(files), 1)

        # check the written mail, and in particular, its X-ZOPE headers
        ob = MailMessage()

        path = os.path.join(tmp_folder, files[0])
        file = open(path, 'r')
        try:
            data = file.read()
        finally:
            file.close()
        ob.loadMessageFromRaw(data)

        raw_msg = ob.getRawMessage().split('\n')
        self.assertEquals(raw_msg[0], 'X-Zope-From: tarek')
        self.assertEquals(raw_msg[1], 'X-Zope-To: bill')
        self.assertEquals(raw_msg[2], 'X-Zope-Hostname: cool.smtp.com')
        self.assertEquals(raw_msg[3], 'X-Zope-Port: 26')
        self.assertEquals(raw_msg[4], 'X-Zope-Username: tarek')
        self.assertEquals(raw_msg[5], 'X-Zope-Password: secret')

    def _createMailer(self, hostname, port, username, password):
        return FakeMailer()

    def test_MailSender(self):
        self.test_MailWriter()
        sender = MailSender(maildir_path)
        smtpmailer._createMailer = self._createMailer
        sender.run(forever=False)

        # should be sent now
        tmp_folder = os.path.join(maildir_path, 'new')
        files = list(os.walk(tmp_folder))[0][2]
        self.assertEquals(len(files), 0)

        tmp_folder = os.path.join(maildir_path, 'cur')
        files = list(os.walk(tmp_folder))[0][2]
        self.assertEquals(len(files), 0)

    def old_test_SmtpMailer(self):
        #XXXX need a realfake smtp here
        # now do the whole thing
        mailer = SmtpMailer(maildir_path)

        # faking
        setMailElement(maildir_path)
        smtpmailer._createMailer = self._createMailer

        # starts to listen
        mailer.start_sender()

        # sends a mail (writing in maildir)
        msg = self.getMailInstance(7)
        msg = msg.getRawMessage()

        mailer.send('tarek', 'bill', msg, 'cool.smtp.com', 26, 'tarek',
                    'secret')

        # wait 1 second
        sleep(1)

        # should be sent now
        tmp_folder = os.path.join(maildir_path, 'new')
        files = list(os.walk(tmp_folder))[0][2]
        self.assertEquals(len(files), 0)

        tmp_folder = os.path.join(maildir_path, 'cur')
        files = list(os.walk(tmp_folder))[0][2]
        self.assertEquals(len(files), 0)

        # stop the thread now
        mailer.stop_sender()

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SMTPMailerTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.smtpmailer'),
        ))

