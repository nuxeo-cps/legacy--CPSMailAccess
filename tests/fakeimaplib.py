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
        return 'OK', 'AUTH'

    def select(self, mailbox):
        pass

    def list(self, directory='""', pattern='*'):
        """ see how to manage this to provide a list
        """
        return ('OK', ['(\\HasNoChildren) "." "INBOX.[Bugs]"', '(\\HasNoChildren) "." "INBOX.[BCEAO]"', '(\\HasNoChildren) "." "INBOX.[interne]"', '(\\HasNoChildren) "." "INBOX.[CPS-users]"', '(\\HasNoChildren) "." "INBOX.Drafts"', '(\\HasNoChildren) "." "INBOX.[dev]"', '(\\HasNoChildren) "." "INBOX.Trash"', '(\\HasNoChildren) "." "INBOX.[TypeMaker]"', '(\\HasNoChildren) "." "INBOX.[CPS-users-fr]"', '(\\HasNoChildren) "." "INBOX.[EuroPython]"', '(\\HasNoChildren) "." "INBOX.[CPS-devel]"', '(\\HasNoChildren) "." "INBOX.[z3-five]"', '(\\HasNoChildren) "." "INBOX.[courier-imap]"', '(\\HasNoChildren) "." "INBOX.[Cps-erp5-sprint]"', '(\\HasNoChildren) "." "INBOX.[Intranet Nuxeo]"', '(\\HasNoChildren) "." "INBOX.Sent"', '(\\HasNoChildren) "." "INBOX.TODO"', '(\\HasNoChildren) "." "INBOX.LOGS"', '(\\HasNoChildren) "." "INBOX.CVS"', '(\\Unmarked \\HasChildren) "." "INBOX"'])

    def search(self, mailbox, charset, *criteria):
        return ('OK', ['1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16'])

class IMAP4_SSL(IMAP4):
    pass