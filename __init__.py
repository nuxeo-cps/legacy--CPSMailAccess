#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
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

import mailbox, mailfolder

def initialize(context):

    context.registerClass(
        mailbox.MailBox,
        constructors = (mailbox.manage_addMailBoxForm,
                        mailbox.manage_addMailBox),
        )

    context.registerClass(
        mailfolder.MailFolder,
        constructors = (mailfolder.manage_addMailFolderForm,
                        mailfolder.manage_addMailFolder),
        )