#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
from zope.testing import doctest
from Testing.ZopeTestCase import ZopeTestCase
from datetime import datetime
from CPSMailAccess.utils import isToday

class UtilsTestCase(ZopeTestCase):

    def test_isToday(self):
        today = datetime(2000, 1, 1)
        today = today.now()
        today_str = today.strftime("%d/%y/%m")

        #self.assert_(isToday(today_str))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UtilsTestCase),
        doctest.DocTestSuite('Products.CPSMailAccess.utils'),
        ))
