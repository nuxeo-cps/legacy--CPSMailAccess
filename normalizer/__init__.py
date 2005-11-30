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
# $Id:$
""" Normalizer package, largely inspired from TextIndexNG
"""
import os
import cmailaccess

# XXX we will use various encoding later
encoding = 'ISO-8859-15'

def getNormalizer(lang='iso'):
    current_path = os.path.dirname(__file__)
    basefilename = '%s.txt' % lang.lower()
    filename = os.path.join(current_path, basefilename)
    files = os.listdir(current_path)
    if not basefilename in files:
        filename = os.path.join(current_path, 'iso.txt')

    normalizers = []
    for line in open(filename):
        if line.strip() == '' or line.strip().startswith('#'):
            continue
        fields = line.split()
        k = unicode(fields[0], encoding)
        v = unicode(fields[1], encoding)
        normalizers.append((k, v))

    return cmailaccess.Normalizer(normalizers)
