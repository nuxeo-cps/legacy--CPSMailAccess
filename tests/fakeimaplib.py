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
        """ XXX we willuse Data subdirectory later here
        """
        message_number = str(message_number)
        if message_number == '1':
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
        result = ('OK', '(UID 123)')
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
        return ('OK', '')

    def create(self, mailbox):
        return ('OK', '')

    def copy(self, msg_num, to_mailbox):
        return ('OK', '')

    def store(self, msg_num, command, value):
        return ('OK', '')

    def expunge(self):
        return ('OK', '')

class IMAP4_SSL(IMAP4):
    pass


