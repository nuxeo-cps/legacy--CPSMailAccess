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
IMAP4_PORT = 25

IMAPError = Exception

class IMAP4:
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

class IMAP4_SSL(IMAP4):
    pass