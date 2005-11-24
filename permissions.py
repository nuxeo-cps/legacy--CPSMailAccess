# -*- coding: ISO-8859-15 -*-
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
try:
    from Products.CMFCore.permissions import setDefaultRoles
except ImportError:
    # BBB for CMF 1.4, remove this in CPS 3.4.0
    from Products.CMFCore.CMFCorePermissions import setDefaultRoles

# Sensible defaults for most permissions
permissions = {
    'View mailbox': ['Owner', 'Manager'],
    'Send mails': ['Owner', 'Manager'],
    'Configure mailbox': ['Owner', 'Manager'],
    'Manage MailTool': ['Owner', 'Manager']
    }

for permission, roles in permissions.items():
    setDefaultRoles(permission, roles)
