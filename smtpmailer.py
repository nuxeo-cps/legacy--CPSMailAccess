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
import os
import socket, threading
import atexit
from smtplib import SMTPRecipientsRefused

from Persistence import Persistent
import Acquisition

from zope.app.mail.mailer import SMTPMailer
from zope.app.mail.delivery import QueueProcessorThread
from zope.app.mail.maildir import Maildir


"""
Asynchronous mail sender system taken from Zope 3
and adapted for CPSMailAccess :

    + MailWriter writes the mail to a MailDir
    + MailSender sends the mailfound in the maildir
    + SmtpMailer orchestrate the things and provides an interface

the difference is that this will work for multiple SMTP servers
"""

def _parseMessage(message):
    """ Extract infos from the message """
    rest = []

    elements = (('fromaddr', 'X-Zope-From'), ('toaddrs', 'X-Zope-To'),
                ('hostname', 'X-Zope-Hostname'), ('port', 'X-Zope-Port'),
                ('username', 'X-Zope-Username'),
                ('password','X-Zope-Password'))
    lines = message.split('\n')
    values = {}

    for element in elements:
        values[element[0]] = None

    # removing bccs
    lines = [line for line in lines if not line.lower().startswith('bcc')]

    for line in lines:
        found = False
        for element in elements:
            if line.startswith(element[1]):
                value = line.replace('%s: ' % element[1], '')
                if value != '' and value != 'None':
                    values[element[0]] = value
                found = True
        if not found:
            rest.append(line)

    return values, '\n'.join(rest)

def _createMailer(hostname, port, username, password):
    """ creates a mailer

    XXX outsourced so we can think of a pool mailer later for optimisation
    """
    return SMTPMailer(hostname, port, username, password)


class MailSender(QueueProcessorThread):
    """ a thread class that sends mail found in a system folder
    """
    def __init__(self, maildir_directory, idle_time=1):
        QueueProcessorThread.__init__(self)
        self.__stopped = True
        # watching folder every second by default
        self.__event = threading.Event()
        self.__interval = idle_time
        self.maildir_directory = maildir_directory
        self.maildir = Maildir(self.maildir_directory, True)

    def run(self, forever=True):
        """ threaded code """
        self.__stopped = False
        while True:
            for filename in self.maildir:
                fromaddr = ''
                toaddrs = ()
                try:
                    file = open(filename)
                    message = file.read()
                    file.close()
                    elements, message = _parseMessage(message)

                    fromaddr = elements['fromaddr']
                    toaddrs = elements['toaddrs'].split(', ')
                    hostname = elements['hostname']
                    port = str(elements['port'])
                    username = elements['username']
                    password = elements['password']

                    mailer = _createMailer(hostname, port, username,
                                                password)
                    mailer.send(fromaddr, toaddrs, message)

                    os.unlink(filename)
                    # TODO: maybe log the Message-Id of the message sent
                    self.log.info("Mail from %s to %s sent.",
                                    fromaddr, ", ".join(toaddrs))
                except:
                    # Blanket except because we don't want
                    # this thread to ever die
                    if fromaddr != '' or toaddrs != ():
                        self.log.error(
                            "Error while sending mail from %s to %s.",
                            fromaddr, ", ".join(toaddrs), exc_info=1)
                    else:
                        self.log.error(
                            "Error while sending mail : %s ",
                            filename, exc_info=1)
            else:
                if forever:
                    self.__event.wait(self.__interval)
                    if self.__stopped:
                        return

            # A testing plug
            if not forever:
                break

    def stop(self):
        self.__stopped = True
        self.__event.set()

    def running(self):
        return not self.__stopped

mail_sender = None

def setMailElement(maildir):
    global mail_sender
    if (mail_sender is None or
        mail_sender.maildir_directory != maildir):
        mail_sender = MailSender(maildir)

def removeMailElement():
    global mail_sender
    if mail_sender is not None:
        mail_sender.stop()

class SmtpMailer(Persistent, Acquisition.Implicit):
    """ a class that delivers a mail to any SMTP server """
    __version__ = (1, 0)

    def __init__(self, maildir_directory, direct_smtp,
                 on_send_mail=''):
        self.maildir_directory = maildir_directory
        self._started = False
        self.direct_smtp = direct_smtp
        self._createMailDir()
        self.mail_trigger = on_send_mail
        self.id = 'smtp_mailer'

    def _createMailDir(self):
        """ creates the maildir """
        if self.direct_smtp != 1:
            # trying to create the maildir
            self.maildir = Maildir(self.maildir_directory, True)
        else:
            self.maildir = None

    def _checkElements(self):
        setMailElement(self.maildir_directory)

    def send(self, fromaddr, toaddrs, message, hostname='localhost', port=25,
             username=None, password=None):
        """ writes the mail mails """
        # XXX security check to avoid a non authoized user
        # to send mails, this will move away when a complete
        # security startegy will be settled
        # (ie: a user loose the right to use his webmail
        # the box stays in the portal, etc..)
        if self.mail_trigger != '':
            # XXX Z2
            pwm = Acquisition.aq_parent(Acquisition.aq_inner(self))
            getattr(pwm, self.mail_trigger)()

        # the first sent ever, wakes everything
        if self.direct_smtp:
            self.stop_sender()
            elements, message = _parseMessage(message)
            mailer = _createMailer(hostname, port, username, password)
            try:
                mailer.send(fromaddr, toaddrs, message)
            except SMTPRecipientsRefused, e:
                return False, e.recipients
            except socket.error, e:
                return False, str(e)
            else:
                return True, ''
        else:
            if self.maildir is None:
                self._createMailDir()

            self.start_sender()
            try:
                self._write(fromaddr, toaddrs, message, hostname, port,
                                  username, password, )
            except SMTPRecipientsRefused, e:
                return False, e.recipients
            else:
                return True, ''

    def stop_sender(self):
        if self.direct_smtp:
            removeMailElement()
        else:
            self._checkElements()
            global mail_sender
            if mail_sender.running():
                mail_sender.stop()

    def start_sender(self):
        """ starts the sender """
        self._checkElements()
        global mail_sender
        if not mail_sender.running():
            mail_sender.start()

    def _string(self, value):
        if isinstance(value, unicode):
            return value.encode('ISO-8859-15')
        return value

    def _write(self, fromaddr, toaddrs, message, hostname='localhost', port=25,
               username=None, password=None):
        """ write the message into the system folder """
        maildir = self.maildir
        msg = maildir.newMessage()

        # making sure we send strings
        fromaddr = self._string(fromaddr)
        toaddrs = self._string(toaddrs)
        hostname = self._string(hostname)
        username = self._string(username)
        password = self._string(password)

        if isinstance(toaddrs, str):
            toaddrs = (toaddrs,)

        # adding headers that will be used by the sender
        msg.write('X-Zope-From: %s\n' % fromaddr)
        msg.write('X-Zope-To: %s\n' % ', '.join(toaddrs))
        msg.write('X-Zope-Hostname: %s\n' % hostname)
        msg.write('X-Zope-Port: %d\n' % port)
        msg.write('X-Zope-Username: %s\n' % username)
        msg.write('X-Zope-Password: %s\n' % password)

        msg.write(message)
        msg.commit()

atexit.register(removeMailElement)
