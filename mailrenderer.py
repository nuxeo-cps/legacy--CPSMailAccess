# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziad� <tz@nuxeo.com>
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

import time
from StringIO import StringIO
from types import StringType, ListType

from email.MIMEAudio import MIMEAudio
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEBase import MIMEBase
from email.MIMEMessage import MIMEMessage
from email.MIMEMultipart import MIMEMultipart
from email import Iterators, Message
from email import Parser
import mimetools
from mimetools import decode

from zope.interface import implements

from utils import decodeHeader, HTMLize, HTMLToText, sanitizeHTML
from interfaces import IMailRenderer


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

        if ptypes.has_key('type'):
            ptype = ptypes['type'].lower()
        else:
            ptype = 'text/plain'

        if ptypes.has_key('charset'):
            pcharset = ptypes['charset']
        else:
            pcharset = 'ISO-8859-15'

        content = self._stringToUnicode(content, pcharset)

        if ptype in ('text/plain', 'text', 'message/rfc822', 'text/html'):
            if part_cte not in ('7bit', '8bit', '', None):
                output_str = StringIO()
                input_str = StringIO(content)
                try:
                    mimetools.decode(input_str, output_str, part_cte)
                    result = output_str.getvalue()
                except ValueError:
                    result = content
            else:
                result = content
            if ptype == 'text/html':
                result = sanitizeHTML(result)
            return result

        if ptype.startswith('multipart'):
            return content

        raise NotImplementedError('part_type %s charset %s type %s content %s' \
                % (part_type, pcharset, ptype, content))

    def _extractBodies(self, mail):
        """ extracts the body """
        part_type = mail['Content-type']

        if part_type is not None and isinstance(part_type, str):
            html = part_type.strip().startswith('text/html')
        else:
            html = False
        part_cte =  mail['Content-transfer-encoding']
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
                part_cte =  mail['Content-transfer-encoding']
                part_type = mail['Content-type']
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
        """ Renders the mail given body part

        Used with a MailMessage *or* or MailPart
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

        if part is None and mail.cache_level == 2:
            # this works for all level
            if mail.isMultipart():
                part_type = mail.getHeader('Content-type')
                if len(part_type) > 0:
                    part_type = part_type[0].lower()
                else:
                    part_type = None
                if part_type is not None and \
                   part_type.startswith('multipart/alternative'):
                    part_count = mail.getPartCount()
                    part = mail.getPart(part_count-1, True)
                else:
                    part = mail.getPart(part_index, True)
            else:
                part = mail.getPart(part_index, True)

        if part is None and mail.cache_level == 1:
            # need to fetch server then
            # but will charge the highest part
            # XXXXX charging into volatile
            # TODO : read the cache configuration, of the message
            # to know if it will get persistent then
            if is_msg:
                volatile = True
                part_str = str(part_index+1)
                if mail.isMultipart():
                    ct = mail.getContentType()
                    if ct.startswith('multipart/alternative'):
                        part_str = '2'

                part = root_msg.loadPart(part_str, part_content='', volatile=volatile)
                html, body = self._extractBodies(part)
            else:
                #need to load the whole branch
                raise NotImplementedError

        else:
            html, body = self._extractBodies(part)

        if not html:
            body = HTMLize(body)
        return body

    def _stringToUnicode(self, string, charset='ISO-8859-15'):
        """ safe string to unicode """
        if not isinstance(string, unicode):
            try:
                result = unicode(string, charset)
            except UnicodeDecodeError:
                # wrong  charset ?
                result = unicode(string, 'ISO-8859-15')
            except LookupError:
                # typically hapenning when wrong charset
                # or when the codec was not installed in python codec
                # forcing iso-8859-15
                result = unicode(string, 'ISO-8859-15')
            return result
        return string
