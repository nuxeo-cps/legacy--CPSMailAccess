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
        try:
            fp = openfile(filename)
            try:
                data = fp.read()                
            finally:
                fp.close()
            
            return data
        except:    
            print str(filename) + ' not found'    
            return ''
               
    def getAllMails(self):
        res = []
        for i in range(35):    
            ob = MailMessage()
            if i < 9:
                data = self._msgobj('msg_0'+str(i+1)+'.txt')
            else:
                data = self._msgobj('msg_'+str(i+1)+'.txt')
                    
            if data <> '':
                try:
                    ob.loadMessage(data)
                    res.append(ob)
                except:
                    pass
        return res                
                                
            
    def getMailInstance(self,number):
        ob = MailMessage()
        
        if number < 9:
            data = self._msgobj('msg_0'+str(number+1)+'.txt')
        else:
            data = self._msgobj('msg_'+str(number+1)+'.txt')   
                
        ob.loadMessage(data)
        return ob
                             
    def test_base(self):
        """ loading a lot of different mails
        """
        ob = MailMessage() 
        for i in range(35):            
            if i < 9:
                data = self._msgobj('msg_0'+str(i+1)+'.txt')
            else:
                data = self._msgobj('msg_'+str(i+1)+'.txt')
                    
            if data <> '':
                try:
                    ob.loadMessage(data)
                except:
                    print '\nmsg_0'+str(i+1)+'.txt fails\n'   
                    

    def test_getPartCount(self):
        """ testing part count on msg_07.txt
        """
        ob = self.getMailInstance(7)                
        part_count = ob.getPartCount()        
        self.assertEquals(part_count, 4)
        
        ob = self.getMailInstance(2)                
        part_count = ob.getPartCount()        
        self.assertEquals(part_count, 1)
        
            
    def test_getCharset(self):
        """ testing charsets on msg_07.txt
        """
        ob = self.getMailInstance(7)
        
        self.assertEquals(ob.getCharset(0), None)
        self.assertEquals(ob.getCharset(1), "us-ascii")
        self.assertEquals(ob.getCharset(2), "iso-8859-1")
        self.assertEquals(ob.getCharset(3), "iso-8859-2")
        
        ob = self.getMailInstance(2)        
        self.assertEquals(ob.getCharset(), None)

 
    def test_getCharset(self):
        """ testing charsets on msg_07.txt
        """
        ob = self.getMailInstance(7)
        self.assertEquals(ob.getCharset(1), "us-ascii")
        ob.setCharset("iso-8859-1", 1)      
        self.assertEquals(ob.getCharset(1), "iso-8859-1")
        
        ob = self.getMailInstance(2)
        self.assertEquals(ob.getCharset(), None)
        ob.setCharset("iso-8859-1")     
        self.assertEquals(ob.getCharset(), "iso-8859-1")
                        
    def test_isMultipart(self):
        """ testing Multipart
        """
        ob = self.getMailInstance(7)
        self.assertEquals(ob.isMultipart(), True)
        
        ob = self.getMailInstance(2)
        self.assertEquals(ob.isMultipart(), False)
        
    def test_getContentType(self):        
        """ testing getContentType
        """
        ob = self.getMailInstance(6)

        ct = ob.getContentType()
        self.assertEquals(ct, 'multipart/mixed')
        
        ct = ob.getContentType(1)
        self.assertEquals(ct, 'text/plain')
        
        ct = ob.getContentType(2)
        self.assertEquals(ct, 'image/gif')

        ob = self.getMailInstance(2)
        
        ct = ob.getContentType()
        self.assertEquals(ct, 'text/plain')
        
        
    def test_setContentType(self):        
        """ testing setContentType
        """
        ob = self.getMailInstance(6)

        ct = ob.getContentType()
        self.assertEquals(ct, 'multipart/mixed')
        ob.setContentType('text/plain')
        ct = ob.getContentType()
        self.assertEquals(ct, 'text/plain')
        
        ct = ob.getContentType(1)
        self.assertEquals(ct, 'text/plain')
        ob.setContentType('image/gif', 1)
        ct = ob.getContentType(1)
        self.assertEquals(ct, 'image/gif')        
                
    def test_getParams(self):        
        """ testing getParams
        """
        ob = self.getMailInstance(6)

        ct = ob.getParams()
        self.assertEquals(ct, [('multipart/mixed', ''), ('boundary', 'BOUNDARY')])
        
        ct = ob.getParam('boundary')
        self.assertEquals(ct, 'BOUNDARY')
        
        ct = ob.getParams(1)
        self.assertEquals(ct, [('text/plain', ''), ('charset', 'us-ascii')])
        
        ct = ob.getParams(2)
        self.assertEquals(ct, [('image/gif', ''), ('name', 'dingusfish.gif')])

        ob = self.getMailInstance(2)
        
        ct = ob.getParams()
        self.assertEquals(ct, None)
        
    def test_setParams(self):        
        """ testing getParams
        """
        ob = self.getMailInstance(6)

        ob.setParam('boundary', 'FRONTIERE')
        ct = ob.getParams()
        self.assertEquals(ct, [('multipart/mixed', ''), ('boundary', 'FRONTIERE')])
        ct = ob.getParam('boundary')
        self.assertEquals(ct, 'FRONTIERE')
        
        ob = self.getMailInstance(2)
        ob.setParam('boundary', 'FRONTIERE')
        ct = ob.getParam('boundary')
        self.assertEquals(ct, 'FRONTIERE')

                                                
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MailMessageTestCase),        
        doctest.DocTestSuite('Products.CPSMailAccess.mailmessage'),
        ))
