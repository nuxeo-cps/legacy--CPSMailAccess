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
import unittest, os
from zope.testing import doctest
from Testing.ZopeTestCase import installProduct
from Testing.ZopeTestCase import ZopeTestCase, _print
from Acquisition import Implicit

from Products.CPSMailAccess.mailtool import MailTool
from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.mailbox import MailBox, IMailBox
from Products.CPSMailAccess.tests import __file__ as landmark
from OFS.Folder import Folder

from email.Errors import BoundaryError
import sys
import fakeimaplib
if sys.modules.has_key('imaplib'):
    del sys.modules['imaplib']
sys.modules['imaplib'] = fakeimaplib

# patching menu registery
from zope.app.publisher.browser.globalbrowsermenuservice \
    import GlobalBrowserMenuService

GlobalBrowserMenuService._menuItem = GlobalBrowserMenuService.menuItem

def menuItem(self, menu_id, interface, action, title,
            description='', filter_string=None, permission=None,
            extra=None,
            ):
    if not self._registry.has_key(menu_id):
        return
    else:
        self._menuItem(menu_id, interface, action, title, description,
                       filter_string, permission, extra)

GlobalBrowserMenuService.menuItem = menuItem

class MailMessageT(MailMessage):
    def getPhysicalPath(self):
        return str(id(self))

installProduct('Five')
#installProduct('TextIndexNG2')

class FakeDirectory:
    def searchEntries(self, return_fields=None, **kw):
        return [('tziade', {'email': 'tz@nuxeo.com',
                 'givenName': 'Tarek', 'sn' : 'Ziadé',
                 'webmail_login' : 'tziade',
                 'webmail_password' : 'do_not_reveal_it_please'})]

    def hasEntry(self, id):
        return False

    def createEntry(self, entry):
        pass

class FakeDirectories(Folder):

    members = FakeDirectory()
    adressbook = FakeDirectory()

    def __init__(self, id=None):
        Folder.__init__(self, id)
        setattr(self, '.addressbook', FakeDirectory())


class FakePortalUrl:
    def getPortalPath(self):
        return 'cps'

    def getRelativeUrl(self, element):
        return 'http://xxx/' + element.absolute_url()

    def __call__(self):
        return 'http://xxx/'

class FakePortal(Folder):

    portal_directories = FakeDirectories('portal_directories')
    portal_url = FakePortalUrl()
    portal_webmail = MailTool()
    maildir_path = os.path.join(os.path.dirname(landmark), 'maildir')

    # no portal wide parameter
    portal_webmail.default_connection_params['max_folder_size'] = (20,0)
    portal_webmail.default_connection_params['uid'] = ('tziade',0)
    portal_webmail.default_connection_params['connection_type'] = ('IMAP',0)
    portal_webmail.default_connection_params['login'] = ('tziade',0)
    portal_webmail.default_connection_params['password'] = ('secret',0)
    portal_webmail.default_connection_params['HOST'] = ('localhost',0)
    portal_webmail.default_connection_params['trash_folder_name'] = ('INBOX.Trash',0)
    portal_webmail.default_connection_params['draft_folder_name'] = ('INBOX.Drafts',0)
    portal_webmail.default_connection_params['sent_folder_name'] = ('INBOX.Sent',0)
    portal_webmail.default_connection_params['smtp_host'] = ('localhost',0)
    portal_webmail.default_connection_params['smtp_port'] = (25,0)
    portal_webmail.default_connection_params['email_adress'] = ('tz@nuxeo.com',0)
    portal_webmail.default_connection_params['max_folder_depth'] = (0,0)
    portal_webmail.default_connection_params['treeview_style'] = ('lotus',0)
    portal_webmail.default_connection_params['message_list_cols'] = (('From', 'Date',
                                                            'Subject', 'Size'),0)
    portal_webmail.default_connection_params['maildir'] = (maildir_path, -1)

    def getPhysicalPath(self):
        return ('', 'nowhere')

class FakeResponse:
    def redirect(self, url):
         pass

class FakeRequest:

    maybe_webdav_client = False

    def getPresentationSkin(self):
        return None

    def get(self, element1, element2):
        return ''

    form = {}
    response = FakeResponse()

def openfile(filename, mode='r'):
    path = os.path.join(os.path.dirname(landmark), 'data', filename)
    return open(path, mode)

class MailTestCase(ZopeTestCase):
    msg_key = 0
    portal = FakePortal()
    request = FakeRequest()

    def setUp(self):
        pass

    def getPhysicalPath(self):
        """ fake getPhysicalPath
        """
        return ('fake',)

    def __init__(self, methodName='runTest'):
        ZopeTestCase.__init__(self, methodName)

    def msgKeyGen(self):
        result = str(self.msg_key)
        self.msg_key += 1
        return result

    def _getMailBox(self, new_instance=False):
        """ testing connector getter
        """
        container = self.portal
        if hasattr(container, 'INBOX'):
            if new_instance:
                mailbox = container.INBOX
                return mailbox
            else:
                container.manage_delObjects(['INBOX'])

        mailbox = MailBox('INBOX')
        container._setObject('INBOX', mailbox)
        mailbox = container.INBOX
        mailbox._connection_params['max_folder_size'] = (20,0)
        mailbox._connection_params['uid'] = ('tziade',0)
        mailbox._connection_params['connection_type'] = ('IMAP',0)
        mailbox._connection_params['login'] = ('tziade',0)
        mailbox._connection_params['password'] = ('secret',0)
        mailbox._connection_params['HOST'] = ('localhost',0)
        mailbox._connection_params['trash_folder_name'] = ('INBOX.Trash',0)
        mailbox._connection_params['draft_folder_name'] = ('INBOX.Drafts',0)
        mailbox._connection_params['sent_folder_name'] = ('INBOX.Sent',0)
        mailbox._connection_params['smtp_host'] = ('localhost',0)
        mailbox._connection_params['smtp_port'] = (25,0)
        mailbox._connection_params['email_adress'] = ('tz@nuxeo.com',0)
        mailbox._connection_params['max_folder_depth'] = (0,0)
        mailbox._connection_params['treeview_style'] = ('lotus',0)
        mailbox._connection_params['message_list_cols'] = (('From', 'Date',
                                                            'Subject', 'Size'),0)
        return mailbox

    def _msgobj(self, filename):
        fp = openfile(filename)
        try:
            data = fp.read()
        finally:
            fp.close()

        return data

    def _openfile(self, filename):
        return openfile(filename)


    def getMailInstance(self, number, raw=False):
        ob = MailMessage()
        if number < 9:
            data = self._msgobj('msg_0'+str(number+1)+'.txt')
        else:
            data = self._msgobj('msg_'+str(number+1)+'.txt')
        ob.loadMessageFromRaw(data)
        if not raw:
            store = ob._getStore()
            while isinstance(store._payload, list):
                store._payload = store._payload[0]._payload
        return ob

    def getMailInstanceT(self, number):
        ob = MailMessageT()
        if number < 9:
            data = self._msgobj('msg_0'+str(number+1)+'.txt')
        else:
            data = self._msgobj('msg_'+str(number+1)+'.txt')
        ob.loadMessageFromRaw(data)
        store = ob._getStore()
        while isinstance(store._payload, list):
            store._payload = store._payload[0]._payload
        return ob

