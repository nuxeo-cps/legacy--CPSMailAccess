# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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
"""
  Functional Tests
"""

from Testing.ZopeTestCase import installProduct
from Products.Five import zcml

# Calling zcml.load_site() in each test_xxx.py will create conflict
# errors if you run more than one test at a time. Doing it in the
# __init__ makes sure it happens once, but only once.
# Also, the product needs to be installed first.

installProduct('CPSMailAccess')
zcml.load_site()