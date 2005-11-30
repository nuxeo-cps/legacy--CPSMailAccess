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
""" setting up C extension module """
from distutils.core import setup, Extension
import sys

extmailaccess = Extension('cmailaccess', sources=['src/cmailaccess.c'])

setup(name = "CPSMailAccessExtensions", version="1.0", author="Tarek Ziadé",
      author_email="tziade@nuxeo.com",
      description="Helper module for quick processing",
      url="http://cps-project.org",
      ext_modules=[extmailaccess])
