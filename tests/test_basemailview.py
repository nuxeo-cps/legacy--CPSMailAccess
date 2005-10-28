# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
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
import unittest
import os

from zope.testing import doctest

from Products.CPSMailAccess.basemailview import BaseMailMessageView
from basetestcase import MailTestCase

class BaseMailViewCase(MailTestCase):

    def test_instance(self):
        mv = BaseMailMessageView(None, None)
        self.assertNotEquals(mv, None)

    def test_lasterror(self):
        box = self._getMailBox()
        res, err = box.testConnection()

        mv = BaseMailMessageView(box, None)
        error = mv._last_error
        self.assertEquals(error, err)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(BaseMailViewCase),
        doctest.DocTestSuite('Products.CPSMailAccess.basemailview'),
        ))
