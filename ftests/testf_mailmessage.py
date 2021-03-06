# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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

import unittest
from Testing.ZopeTestCase import FunctionalTestCase
from Testing.ZopeTestCase import user_name, folder_name

class MailMessageTest(FunctionalTestCase):

    def afterSetUp(self):
        user = self.folder.acl_users.getUser(user_name)
        user.roles.append('Manager')

    def test_addMessage(self):
        """ testing mailbox adding
        """
        response = self.publish( '/%s/manage_addProduct/CPSMailAccess/' \
           'manage_addMailMessage' % folder_name,
            basic='%s:secret'% user_name,
            extra={'id':'my_message',
                   'submit_edit': 'Add'})

        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('location'),
                         'http://nohost/%s/my_message/manage_main' % folder_name)

    # This test will fail as there is no main_template around in this
    # test environment.
    #def test_ViewMessage(self):
        #""" testing message view
        #"""
        #self.test_addMessage()
        #response = self.publish(
            #'/%s/my_message/view' % folder_name,
            #basic='%s:secret'% user_name
        #)
        #self.assertEqual(response.getStatus(), 200)

        #body = response.getBody()

        ## testing structure
        #self.assert_(body.find('body') > 0)
        #self.assert_(body.find('<div id="mailSubject">') > 0)
        #self.assert_(body.find('<div id="mailFrom">') > 0)
        #self.assert_(body.find('<div id="mailTo">') > 0)
        #self.assert_(body.find('<div id="mailBody">') > 0)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
