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
from utils import decodeHeader, HTMLize, HTMLToText, sanitizeHTML
import mimetools
from cStringIO import StringIO

EMPTYSTRING = ''

class MailRenderer:
    """A tool to render MIME parts

    >>> f = MailRenderer()
    >>> IMailRenderer.providedBy(f)
    True
    """
    implements(IMailRenderer)

    def extractPartTypes(self, part_type):
        if part_type is None:
            return {'type' : 'text/plain'}
        ptypes = {}
        types = part_type.split(';')
        for ptype in types:
            if ptype.find('=') > -1:
                parts = ptype.split('=')
                name = parts[0].strip()
                value = parts[1].strip()
                value = value.strip('"')
                ptypes[name] = value
            else:
                ptypes['type'] = ptype.strip()

        return ptypes


    def render(self, content, part_type, part_cte):
        """ renders a body according to part type """
        if content is None:
            return ''

        ptypes = self.extractPartTypes(part_type)
        ptype = ptypes['type']
        if ptypes.has_key('format'):
            pformat = ptypes['format']
        else:
            pformat = ''
        if ptypes.has_key('charset'):
            pcharset = ptypes['charset']
        else:
            pcharset = 'ISO-8859-15'

        if ptype in ('text/plain', 'text', 'message/rfc822', 'text/html'):

            if part_cte not in ('7bit', '8bit', '', None):
                result = StringIO(u'')
                mimetools.decode(content, result, part_cte)
            else:
                result = content

            if ptype == 'text/html':
                result = sanitizeHTML(result)

            if not isinstance(result, unicode):
                try:
                    result = unicode(result, pcharset)
                except LookupError:
                    # typically hapenning when wrong charset
                    # or when the codec was not installed in python codec
                    # forcing iso-8859-15
                    result = unicode(result, 'ISO-8859-15')
            return result

        if ptype.startswith('multipart'):
            if not isinstance(content, unicode):
                return unicode(content, pcharset)
            else:
                return content

        raise NotImplementedError('part_type %s charset %s type %s \n content %s' \
                % (part_type, pcharset, ptype, content))

    def _extractBodies(self, mail):
        """ extracts the body """
        part_type = mail['Content-type']
        if part_type is not None and isinstance(part_type, str):
            html = part_type.strip().startswith('text/html')
        else:
            html = False
        part_cte =  mail['Content-transfert-encoding']
        if mail.is_multipart():
            # have to choose an alternative here
            if part_type is not None and \
                part_type.startswith('multipart/alternative'):
                # always choose the last one (html rendering)
                last = len(mail._payload) - 1
                mail = mail._payload[last]
                sub_part_type = mail['Content-type']
                if sub_part_type is not None and \
                   isinstance(sub_part_type, str):
                    html = sub_part_type.strip().startswith('text/html')
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

        if res is None:
            # body is empty
            return False, ''
        else:
            return html, self.render(res, part_type, part_cte)


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
                html, body = self._extractBodies(part)
            else:
                #need to load the whole branch
                raise NotImplementedError

        else:
            html, body = self._extractBodies(part)

        if not html:
            body = HTMLize(body)

        return body
