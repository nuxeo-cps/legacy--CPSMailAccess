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
""" fakesmtplib provided for testings
"""
is_fake = 1

class SMTPException(Exception):
    pass

class SMTP:
    host = ''
    port = 25
    def __init__(self, host, port=25):
        self.host = host
        self.port = port

    def sendmail(self, from_addr, to_addrs, msg,
            mail_options=[], rcpt_options=[]):
        pass

    def quit(self):
        pass
