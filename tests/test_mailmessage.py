# Copyright (C) 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
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
from Testing.ZopeTestCase import ZopeTestCase

from Products.CPSMailAccess.mailmessage import MailMessage
from Products.CPSMailAccess.interfaces import IMailMessage

from CPSMailAccess.tests import __file__ as landmark

installProduct('FiveTest')
installProduct('Five')


def openfile(filename, mode='r'):
    path = os.path.join(os.path.dirname(landmark), 'data', filename)
    return open(path, mode)

    
class MailMessageTestCase(ZopeTestCase):    
    
    
    
    def _msgobj(self, filename):
        fp = openfile(filename)
        try:
            data = fp.read()
        finally:
            fp.close()
        
        return data
        
    def test_base(self):
        """ loading a mail
        """
        ob = MailMessage() 
        data = self._msgobj('msg_01.txt')
        ob.loadMessage(data)
        
        
            
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageTestCase),        
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessage'),
        ))
