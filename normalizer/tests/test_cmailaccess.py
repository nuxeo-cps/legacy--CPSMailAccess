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
#
# $Id$
""" XXX doctest is ran this way to work under Python 2.3
"""
import os
import doctest
import unittest

def doc_test():
    """
    ------------------------
    CPSMailAccess Extensions
    ------------------------

    CPSMailAccess uses a C extension module called `cmailmaccess` to speed up
    some process.

    Some code will slowly move into cmailaccess to optimize mail indexing and
    searching.

    The first C element is the normalizer, used to clean up words that get
    indexed, in order to be able to find mails with special characters.

    the module is installed in the python ran by Zope::
        >>>
        >>> try:
        ...     from cmailaccess import Normalizer
        ... except ImportError:
        ...     from Products.CPSMailAccess.normalizer import Normalizer

    cmailaccess.Normalizer is an object that takes a sequence of normalizers
    at construction. A normalizer is a two string tuple (actual, normalized)::

        >>> converters = [('é', 'e'), ('à', 'a'), ('ù', 'u')]
        >>> normalizer = Normalizer(converters)

    the instance then provide a `normalize(word)` method::

        >>> normalizer.normalize('éééàà ùù')
        u'eeeaa uu'
        >>> normalizer.normalize('eeee')
        u'eeee'
        >>> normalizer.normalize(u'éééàà ùù')
        u'eeeaa uu'
        >>> normalizer.normalize(u'eeee')
        u'eeee'

    """


def test_suite():
    suite = doctest.DocTestSuite(__name__)
    return unittest.TestSuite((suite,))
