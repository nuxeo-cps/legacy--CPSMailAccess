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
from zLOG import LOG, INFO, DEBUG
from email.MIMEAudio import MIMEAudio
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEBase import MIMEBase
from email.MIMEMessage import MIMEMessage
from email.MIMEMultipart import MIMEMultipart
from email import Iterators, Message
from interfaces import IMailRenderer
from zope.interface import implements
from mimetools import decode
from email import Parser
from types import StringType, ListType

EMPTYSTRING = ''

class MailRenderer:
    """A tool to render MIME parts

    >>> f = MailRenderer()
    >>> IMailRenderer.providedBy(f)
    True
    """
    implements(IMailRenderer)

    def _extractBodies(self, mail):
        """ extracts the body
        """
        if mail.is_multipart():
            it = Iterators.body_line_iterator(mail)
            lines = list(it)
            res = EMPTYSTRING.join(lines)
        else:
            # check if there's sub parts
            payload = mail.get_payload()
            if isinstance(payload, ListType):
                # XXXwe'll need deeper extraction here
                res = payload
            else:
                res = payload
        return res

    def renderBody(self, mail, part_index=0):
        """ renders the mail given body part
            used with a MailMessage *or* or MailPart
            XXX still unclear if we want to split this in
            two renderers : one for part, one for msg
        """
        if mail is None:
            return ''
        # ugly
        is_msg = hasattr(mail, 'getVolatilePart')
        if not is_msg:
            root_msg = mail.msg
        else:
            root_msg = mail
        # volatile ?
        # a sub part cannot be obtained thru the root
        # so this is only for the first level
        if is_msg:
            part = mail.getVolatilePart(part_index)
        if part is None:
            # this works for all level
            part = mail.getPart(part_index, True)
        if part is None:
            # need to fetch server then
            # but will charge the highest part
            # XXXXX charging into volatile
            # TODO : read the cache configuration, of the message
            # to know if it will get persistent then
            if is_msg:
                volatile = True
                part = root_msg.loadPart(part_index, part_content='', volatile=volatile)
                return self._extractBodies(part)
            else:
                #need to load the whole branch
                raise NotImplementedError

        return self._extractBodies(part)
