# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
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
# $Id$
""" Smtp mailer
    TODO: used zope 3 threaded queue mail delivery
    utility thru zcml directive
    and get notification when swork is done
"""

from zope.app.mail.mailer import SMTPMailer
from zope.app.mail.delivery import QueuedMailDelivery
from zope.interface import implements
from smtplib import SMTPRecipientsRefused

class MultiSMTPMailer(SMTPMailer):
    """ a class that delivers a mail to any SMTP server """

    def send(self, fromaddr, toaddrs, message, hostname='localhost', port=25,
             username=None, password=None):
        """ sets SMTP infos then sends the mail
        """

        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        SMTPMailer.send(self, fromaddr, toaddrs, message)

class SmtpQueuedMailer(object):
    """ a class that sends mails """

    mailer = MultiSMTPMailer()

    def send(self, fromaddr, toaddrs, message, hostname='localhost', port=25,
             username=None, password=None):
        """ sends mails """

        try:
            self.mailer.send(fromaddr, toaddrs, message, hostname, port,
                         username, password, )
        except SMTPRecipientsRefused, e:
            return False, e.recipients
        else:
            return True, ''
