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
# $Id
from zope.app.mail.delivery import QueuedMailDelivery
from zope.app.mail.mailer import SMTPMailer
from zope.app.mail.interfaces import IMailQueueProcessor
from zope.interface import implements

from smtplib import SMTP

class SmtpQueuedMailer:
    """ a class that implements IMailQueueProcessor
        and sends mails with various indentitites
    """
    implements(IMailQueueProcessor)

    queuePath = ''
    pollingInterval = 500
    mailer = SMTPMailer()
    delivery = None

    def __init__(self, queuePath):
        self.delivery = QueuedMailDelivery(queuePath)

    def sendMail(self, host, port, user_id, password, \
        fromaddr, toaddrs, message):
        """ next : uses IMailQueueProcessor and
            QueuedMailDelivery when
            founded how to make it work with multi smtp
        """
        server = SMTP(host, port)
        res = server.sendmail(fromaddr, toaddrs, message)
        server.quit()
        if res != {}:
            # TODO: look upon failures here
            pass

        return True
