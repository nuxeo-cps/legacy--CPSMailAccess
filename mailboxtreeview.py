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
# $Id$
""" MailBoxTreeView
    A MailBoxTreeView shows a treeview
    from the mail box
"""
# XX see for dependencies
from Products.CPSDefault.TextBox import TextBox

class MailBoxTreeView(TextBox):

    meta_type = 'MailBoxTreeView'
    portal_type = meta_type

    def __init__(self, id, category='mailboxtreeview', **kw):
        TextBox.__init__(self, id, category=category, **kw)
