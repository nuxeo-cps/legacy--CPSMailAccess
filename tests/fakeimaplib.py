# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziadé <tz@nuxeo.com>
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
""" fakeimap provided for testings
"""
is_fake = 1
IMAP4_PORT = 25
IMAP4_SSL_PORT = 993
IMAPError = Exception

class FakeSocket:
    def settimeout(self, time):
        pass

class IMAP4:
    abort = IMAPError
    state = 'NOAUTH'

    def __init__(self, host='', port=25):
        self.host = host
        self.port = port

    def noop(self):
        pass

    def error(self):
        raise IMAPError

    def login(self, user, password):
        self.user= user
        self.password = password
        self.state = 'AUTH'
        return ('OK', 'AUTH')

    def select(self, mailbox):
        pass

    def fetch(self, message_number, message_part):
        """ XXX we will use Data subdirectory later here
        """
        message_number = str(message_number)

        if message_number == '37809' and message_part == '(BODY)':
            return ('OK', ['1250 (UID 37809 BODYSTRUCTURE ((("text" "plain" ("charset" "us-ascii" "format" "flowed") NIL NIL "quoted-printable" 539 16 NIL ("inline" NIL) NIL)("application" "pgp-signature" NIL NIL NIL "7bit" 193 NIL NIL NIL) "signed" ("micalg" "pgp-sha1" "protocol" "application/pgp-signature" "boundary" "==========76E8B402BF692A9541DA==========") NIL NIL)("text" "plain" ("charset" "us-ascii") NIL NIL "7bit" 300 7 NIL ("inline" NIL) NIL) "mixed" ("boundary" "===============2046136533==") NIL NIL))'])

        if message_number == '1':
            if message_part.startswith('(FLAGS RFC822.SIZE BODY.PEEK[HEADER.FIELDS('):

                return ('OK', [('1 (FLAGS (\\Answered \\Seen) RFC822.SIZE 1766 BODY[HEADER.FIELDS ("From" "To" "Cc" "Subject" "Date" "Message-ID" "In-Reply-To" "Content-Type")] {242}', 'Message-ID: <410F430F.8060308@nuxeo.com>\r\nDate: Tue, 03 Aug 2004 09:47:27 +0200\r\nFrom: Stefane Fermigier <sf@nuxeo.com>\r\nTo: tziade@nuxeo.com\r\nSubject: Test\r\nContent-Type: multipart/mixed;\r\n boundary="------------060003030709020505030207"\r\n\r\n'), ')'])

            if message_part == '(FLAGS RFC822.SIZE RFC822.HEADER)':
                return ('OK', [('1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'), ')'])


            if message_part == '(FLAGS RFC822)':
                return ('OK',[('1 (FLAGS (\\Seen) RFC822.SIZE 515 RFC822.HEADER {474}', 'Return-Path: <webmaster@zopeur.org>\r\nDelivered-To: webmaster@openconference.org\r\nReceived: (qmail 28847 invoked by uid 508); 1 Jan 2005 01:31:52 -0000\r\nMessage-ID: <20050101013152.24339.qmail@ns2641.ovh.net>\r\nFrom: webmaster@openconference.org\r\nTo: webmaster@openconference.org\r\nSubject: webmaster@openconference.org\r\nDate: Sat, 01 Jan 2005 02:31:52 +0100\r\nMime-Version: 1.0\r\nContent-Type: text/plain; format=flowed; charset="iso-8859-1"\r\nContent-Transfer-Encoding: 8bit\r\n\r\n'), ')'])

            if message_part == '(BODYSTRUCTURE)':
                return ('OK',['1 (BODYSTRUCTURE ("text" "plain" ("format" "flowed" "charset" "iso-8859-1") NIL NIL "8bit" 41 4 NIL NIL NIL))'])
            if message_part == '(BODY)':
                return ('OK',['2 (BODY ((("text" "plain" ("charset" "us-ascii") NIL NIL "8bit" 738 18)("text" "html" ("charset" "us-ascii") NIL NIL "8bit" 0 0) "alternative")("image" "jpeg" ("name" "wlogo.jpg") NIL NIL "base64" 7226) "mixed"))'])
            if message_part == '(FLAGS)':
                return ('OK',[('1 (FLAGS (\\Seen)'), ')'])

        if message_number.find(',') != -1:
            if message_part.startswith('(FLAGS RFC822.SIZE BODY.PEEK[HEADER.FIELDS('):

                return ('OK', [('1 (FLAGS (\\Answered \\Seen) RFC822.SIZE 1766 BODY[HEADER.FIELDS ("From" "To" "Cc" "Subject" "Date" "Message-ID" "In-Reply-To" "Content-Type")] {242}', 'Message-ID: <410F430F.8060308@nuxeo.com>\r\nDate: Tue, 03 Aug 2004 09:47:27 +0200\r\nFrom: Stefane Fermigier <sf@nuxeo.com>\r\nTo: tziade@nuxeo.com\r\nSubject: Test\r\nContent-Type: multipart/mixed;\r\n boundary="------------060003030709020505030207"\r\n\r\n'), ')', ('2 (FLAGS (\\Seen) RFC822.SIZE 661181 BODY[HEADER.FIELDS ("From" "To" "Cc" "Subject" "Date" "Message-ID" "In-Reply-To" "Content-Type")] {274}', 'Message-ID: <4110A6E4.5090607@zopeur.org>\r\nDate: Wed, 04 Aug 2004 11:05:40 +0200\r\nFrom: =?ISO-8859-1?Q?Tarek_Ziad=E9?= <webmaster@zopeur.org>\r\nTo: tz@nuxeo.com\r\nSubject: [Fwd: Specs BCEAO]\r\nContent-Type: multipart/mixed;\r\n boundary="------------090103050002020902020908"\r\n\r\n'), ')'])


        raise 'could not fake msg number "%s" part "%s"' %(message_number, message_part)
        return result

    def list(self, directory='""', pattern='*'):
        """ see how to manage this to provide a list
        """
        return ('OK',
                ['(\\HasNoChildren) "." "INBOX.[Bugs]"',
                 '(\\HasNoChildren) "." "INBOX.[BCEAO]"',
                 '(\\HasNoChildren) "." "INBOX.[interne]"',
                 '(\\HasNoChildren) "." "INBOX.[CPS-users]"',
                 '(\\HasNoChildren) "." "INBOX.Drafts"',
                 '(\\HasNoChildren) "." "INBOX.[dev]"',
                 '(\\HasNoChildren) "." "INBOX.Trash"',
                 '(\\HasNoChildren) "." "INBOX.[TypeMaker]"',
                 '(\\HasNoChildren) "." "INBOX.[CPS-users-fr]"',
                 '(\\HasNoChildren) "." "INBOX.[EuroPython]"',
                 '(\\HasNoChildren) "." "INBOX.[CPS-devel]"',
                 '(\\HasNoChildren) "." "INBOX.[z3-five]"',
                 '(\\HasNoChildren) "." "INBOX.[courier-imap]"',
                 '(\\HasNoChildren) "." "INBOX.[Cps-erp5-sprint]"',
                 '(\\HasNoChildren) "." "INBOX.[Intranet Nuxeo]"',
                 '(\\HasNoChildren) "." "INBOX.Sent"',
                 '(\\HasNoChildren) "." "INBOX.TODO"',
                 '(\\HasNoChildren) "." "INBOX.LOGS"',
                 '(\\HasNoChildren) "." "INBOX.CVS"',
                 '(\\Unmarked \\HasChildren) "." "INBOX"',
                 ])

    def search(self, mailbox, charset, *criteria):
        return ('OK', ['1'])

    def append(self, mailbox, flags, date_time, message):
        return ('OK', ['', ''])

    def partial(self, message_num, message_part, start, length):
        return ('OK', '')

    def rename(self, oldmailbox, newmailbox):
        return ('OK', '')

    def uid(self, command, *args):
        if hasattr(self, command):
            command = getattr(self, command)
            return command(*args)
        else:
            return self.fetch('OK', '')

    def create(self, mailbox):
        return ('OK', '')

    def delete(self, mailbox):
        return ('OK', '')

    def copy(self, msg_num, to_mailbox):
        return ('OK', '')

    def store(self, msg_num, command, value):
        return ('OK', '')

    def expunge(self):
        return ('OK', '')

    def socket(self):
        return FakeSocket()

    def response(self, command):
        return (command, [None])

class IMAP4_SSL(IMAP4):
    pass


