# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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
""" a few utilities
"""
import os, os.path
import string, re, md5
from sgmllib import SGMLParseError
from threading import Thread
from email.Header import decode_header, make_header
from email.Errors import HeaderParseError
from exceptions import UnicodeDecodeError
from datetime import datetime
from time import localtime
from random import randrange
from email.Utils import fix_eols, parsedate_tz, mktime_tz
from encodings import exceptions as encoding_exceptions
from DateTime import DateTime
from Acquisition import aq_get

from zope.app.datetimeutils import DateTimeParser, \
    SyntaxError as ZSyntaxError, DateTimeError
from Products.CPSUtil.html import HTMLSanitizer

_translation_table = string.maketrans(
    # XXX candidates: @�+=`|
    '"' r"""'/\:; &�������������������������������������������������������""",
    '_' r"""_______AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuyy""")

_ok_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_."


def makeId(string, lower=0, encoding='ISO-8859-15'):
    "Make id from string"
    if isinstance(string, unicode):
        string = string.encode(encoding)
    id = string.translate(_translation_table)
    id = id.replace('�', 'AE')
    id = id.replace('�', 'ae')
    id = id.replace('�', 'OE')
    id = id.replace('�', 'oe')
    id = id.replace('�', 'ss')
    id = ''.join([c for c in id if c in _ok_chars])
    id = re.sub('_+', '_', id)
    while id.startswith('_') or id.startswith('.'):
        id = id[1:]
    while id.endswith('_'):
        id = id[:-1]
    if not id:
        # Fallback if empty or incorrect
        newid = str(int(DateTime())) + str(randrange(1000, 10000))
        return newid
    if lower:
        id = id.lower()
    return id


def uniqueId(container, seed='', use_primary=True):
    """ returns a unique ID for a subobject
    """
    if use_primary:
        primary_id = makeId(seed)
        if not primary_id in container.objectIds():
            return primary_id
    i = 0
    # XXX linear time !
    while seed + str(i) in container.objectIds():
        i +=1

    return makeId(seed + str(i))

def md5Hash(element):
    """ returns a md5 key
    """
    m = md5.new()
    m.update(element)
    return m.hexdigest()

def decodeHeader(header, encoding='ISO8859-15'):
    """ decodes a mail header """
    # python 2.3 email Header.py works with strings
    # we don't !
    if isinstance(header, unicode):
        header = header.encode(encoding)

    try:
        decoded_header = decode_header(header)
    except HeaderParseError:
        return header

    cdecoded_header = []
    for part in decoded_header:
        if part[1] is None and encoding is not None:
            cdecoded_header.append((part[0], encoding))
        else:
            cdecoded_header.append((part[0], part[1]))

    # controling encodings
    try:
        hu = make_header(cdecoded_header)
        hu = hu.__unicode__()
    except (encoding_exceptions.LookupError, UnicodeDecodeError):
        # unknown encoding or uninstalled (iso-2022-jp maybe)
        # we'll do iso here
        cdecoded_header = []
        for part in decoded_header:
            cdecoded_header.append((part[0], 'ISO8859-15'))
        hu = make_header(cdecoded_header)
        hu = hu.__unicode__()
    return hu


def parseDateString(date_string):
    """ parses a string to render a localized date """
    tm = parsedate_tz(date_string)
    if tm is not None:
        tm = mktime_tz(tm)
        localized = localtime(tm)
    else:
        # the time does not follow RFC 2822
        # let's try to guess it with z3 DateTimeParser
        try:
            localized = DateTimeParser().parse(date_string)
        except (ZSyntaxError, DateTimeError):
            localized = (1970, 1, 1, 0, 0, 0)

    return datetime(localized[0], localized[1], localized[2],
                     localized[3], localized[4], localized[5])


def localizeDateString(date_string, format=0, lang='en'):
    """ normalizes renders a localized date string """
    date = parseDateString(date_string)
    if format == 1:
        return date.strftime('%H:%M')
    elif format == 2:
        return date.strftime('%d/%m')
    elif format == 3:
        return date.strftime('%d/%m/%y')
    else:
        import locale
        # save current locale
        lang = '%s_%s' %(lang, lang.upper())
        old_local = locale.getlocale(locale.LC_TIME)
        if old_local != lang:
            try:
                locale.setlocale(locale.LC_TIME, lang)
            except locale.Error:
                lang = old_local
        try:
            return date.strftime('%a %d/%m/%y %H:%M').title()
        finally:
            if old_local != lang:
                if old_local != (None, None):
                    try:
                        locale.setlocale(locale.LC_TIME, old_local)
                    except locale.Error:
                        locale.setlocale(locale.LC_TIME, '')
                else:
                    locale.setlocale(locale.LC_TIME, '')

def isToday(date_string):
    """ tells if the given string represents today's date
    """
    date = parseDateString(date_string)
    today = date.now()
    return date.year == today.year and date.month ==today.month\
     and date.day == today.day

def truncateString(element, font_size, max_size):
    """ truncates the string according to the given maximum size
        this is an aproximation since
        caracter width can vary
    >>> truncateString('coucou', 10, 57)
    'co...'
    >>> truncateString('coucou', 10, 89)
    'coucou'
    >>> truncateString('coucou', 10, 20)
    '...'
    >>> truncateString('coucou', 90, 90)
    '...'
    >>> truncateString('ok', 2, 90)
    'ok'
    """
    if len(element) * font_size > max_size:
        sub_max = max_size - (3*font_size)
        if sub_max<=0:
            return '...'
        sub_max = int(sub_max/ font_size)
        return element[:sub_max]+'...'
    else:
        return element

def mimetype_to_icon_name(mimetype):
    """ transforms a mimetype to an icon filename
        used for attached files
    >>> mimetype_to_icon_name('image/gif')
    'image_gif.png'
    >>> mimetype_to_icon_name('')
    'unknown.png'
    """
    current_rep = os.path.dirname(__file__)
    current_skin_rep = os.path.join(current_rep, 'skins', 'mime_icons')
    try:
        registered_icons = os.listdir(current_skin_rep)
    except IOError:
        registered_icons = []

    if mimetype.strip() == '':
        return 'unknown.png'

    filename = mimetype.replace('/', '_')+'.png'

    if filename in registered_icons:
        return filename
    else:
        return 'unknown.png'

def getFolder(mailbox, folder_name):
    current = mailbox
    path = folder_name.split('.')
    for element in path:
        element = element.strip()
        element_id = makeId(element)
        if not hasattr(current, element_id):
            return None
        current = getattr(current, element_id)
    return current

_marker = object()
def getToolByName(obj, name, default=_marker):
    try:
        tool = aq_get(obj, name, default, 1)
    except AttributeError:
        if default is _marker:
            raise
        return default
    else:
        if tool is _marker:
            raise AttributeError, name
        return tool

def replyToBody(from_value, body, line_header='> '):
    """ return a reply bloc """
    # comes from CPS so ISO-8859-15
    # making sure we're all unicode
    if not isinstance(body, unicode):
        body = body.decode('ISO-8859-15')

    if not isinstance(from_value, unicode):
        from_value = from_value.decode('ISO-8859-15')

    # remove all html tags and check body
    # special case
    from_value_res = removeHTML(from_value).strip()
    if from_value_res == '':
        from_value_res = extractMailParts(from_value)
        if len(from_value_res) == 1:
            from_value = from_value_res[0]
    else:
        from_value = from_value_res

    body = verifyBody(body)
    body = removeHTML(body)
    body_lines = body.split('\r\n')

    reply_content = [line_header + from_value + u' wrote']
    for line in body_lines:
        reply_content.append(line_header+line)
    return '\r\n'.join(reply_content)

def verifyBody(body):
    """ verify direct body content, according to
        content-type
    """
    try:
        body = fix_eols(body)
        body = body.replace('&lt;', '<')
        body = body.replace('&gt;', '>')
        body = body.replace('<br/>', '\r\n')
        ### epoz :(
        body = body.replace('<br>', '\r\n')
    except TypeError:
        pass
    return body

def HTMLize(content):
    """ transforms a text into a html bloc """
    content = fix_eols(content)
    content = content.replace('<', '&lt;')
    content = content.replace('>', '&gt;')
    content = content.replace('\r\n', '<br/>')
    return content

def cleanUploadedFileName(filename):
    """ cleans filename from its path
        this needs to work on any server (it's a client side file)
    >>> cleanUploadedFileName('C:\Windows\Desktop\Internet Explorer.lnk')
    'Internet Explorer.lnk'
    >>> cleanUploadedFileName('/home/ghjk/fghjkl.gif')
    'fghjkl.gif'
    >>> cleanUploadedFileName('fghjkl.gif')
    'fghjkl.gif'
    >>> cleanUploadedFileName('')
    ''
    """
    if filename.find(':\\') != -1:
        splitted = filename.split('\\')
    else:
        splitted = filename.split('/')

    return splitted[-1]

class HTMLMailSanitizer(HTMLSanitizer):
    """ very tolerant sanitizer
        for the mail to render
        like it's intended
    """
    tags_to_keep = ('b', 'i', 'strong', 'br', 'p', 'h1', 'h2', 'h3',
                    'h4', 'h5', 'div', 'span', 'table', 'tr', 'th', 'td',
                    'font', 'style', 'img', 'ul', 'li', 'hr',
                    'em', 'strong','q', 'cite', 'abbr', 'acronym',
                    'address', 'blockquote')

    tolerant_tags = ('br', 'p')
    attributes_to_keep = ('size', 'face', 'class', 'src', 'href', 'type', 'border')
    attributes_to_remove = ('accesskey', 'onclick')

def sanitizeHTML(content):
    """ satinize html """
    work = content.replace('&lt;', '<')
    work = work.replace('&gt;', '>')
    # thunderbid's html has \n instead of \r\n
    work = fix_eols(work)
    work = work.replace('\r\n', '')    # nothing to care about in HTML

    parser = HTMLMailSanitizer()
    parser.feed(work)
    parser.close()
    parser.cleanup()
    return ''.join(parser.result)

class HTMLExtraction(HTMLSanitizer):
    tags_to_keep = ('br', )
    attributes_to_keep = ()

def removeHTML(content):
    """ remove html """
    work = content.replace('&lt;', '<')
    work = work.replace('&gt;', '>')
    # thunderbid's html has \n instead of \r\n
    work = fix_eols(work)
    # in case there are line feeds, we replace them with brs
    work = work.replace('\r\n', '<br>')

    parser = HTMLExtraction()
    try:
        parser.feed(work)
    except SGMLParseError:
        return content
    parser.close()
    parser.cleanup()
    result = ''.join(parser.result)
    result = result.replace('<br>', '\r\n')
    return result

def isValidEmail(mail):
    """ verifies a mail is a mail """
    #re_script = r'.*@.*\..{2,4}'
    re_script = r'.*@.*'    # tarek@localhost works too
    res = re.match(re_script, mail.strip())
    if res is None:
        return False
    res = res.group(0)
    return res == mail.strip()

def extractMailParts(mail):
    """ extracts parts
    >>> extractMailParts('Tarek Ziade <tz@nuxeo.com>')
    ['Tarek Ziade', 'tz@nuxeo.com']
    >>> extractMailParts('Tarek Ziade     <tz@nuxeo.com > ')
    ['Tarek Ziade', 'tz@nuxeo.com']
    >>> extractMailParts('<tz@nuxeo.com>')
    ['tz@nuxeo.com']
    >>> extractMailParts('tz@nuxeo.com')
    ['tz@nuxeo.com']
    """
    re_script = r'(.*)(<.*>)'
    res = re.findall(re_script, mail.strip())
    if len(res) == 0:
        return [mail.strip()]
    else:
        res = list(res[0])
        res[0] = res[0].strip()
        if len(res) > 1:
            email = res[1].strip()
            email = email[1:-1]
            res[1] = email.strip()
        if res[0] == '':
            del res[0]
        return res

def sameMail(mail1, mail2):
    """ tells if the recipients are the same

    Works even if the presentation differs

    >>> sameMail('Tarek Ziad� <tz@nuxeo.com>', 'tz@nuxeo.com')
    True
    >>> sameMail('Tarek Ziad� <tz@nuxeo.com>', 'TZ@NUXEO.COM')
    True
    >>> sameMail('<tz@nuxeo.com>', 'tz@nuxeo.com ')
    True
    >>> sameMail('<tz@nuxeo.com>', 'john@doe.com ')
    False
    >>> sameMail('<tz@nuxeo.com>', '     tz@nuxeo.com              ')
    True
    """
    re_script = r'<.*>'

    res = re.findall(re_script, mail1.strip())
    if len(res) > 0:
        mail1 = res[0][1:-1].strip()

    res = re.findall(re_script, mail2.strip())
    if len(res) > 0:
        mail2 = res[0][1:-1].strip()

    mail1 = mail1.lower()
    mail2 = mail2.lower()

    return mail1.strip(' ') == mail2.strip(' ')

def getHumanReadableSize(octet_size):
    """ returns a human readable file size """
    if (octet_size is None or octet_size == ''):
        return (-1, '')

    if not isinstance(octet_size, int):
        if not isinstance(octet_size, str):
            raise Exception('need an integer')
        else:
            octet_size = int(octet_size)

    mega = 1024*1024
    kilo = 1024

    if octet_size is None or octet_size <= 0:
        return (0, '')
    elif octet_size >= mega:
        if octet_size == mega:
            return (1, 'mo')
        else:
            msize = float(octet_size/float(mega))
            msize = int(msize)
            return (msize, 'mo')
    elif octet_size >= kilo:

        if octet_size == kilo:
            return (1, 'ko')
        else:
            msize = float(octet_size/float(kilo))
            msize = int(msize)
            return (msize, 'ko')
    else:
        if octet_size == 1:
            return (1, 'o')
        else:
            return (octet_size ,'o')

def intToSortableStr(values):
    """ takes an integer and returns a string that can be sorted

    >>> serie = [1, 123, 768, 988765, 65]
    >>> intToSortableStr(serie)
    ['000001', '000123', '000768', '988765', '000065']
    """
    strings = [str(value) for value in values]
    max_ = 0
    for value in strings:
        if len(value) > max_:
            max_ = len(value)
    fvalues = []
    for value in strings:
        while len(value) < max_:
            value = '0' + value
        fvalues.append(value)
    return fvalues

class AsyncCall(Thread):
    def __init__(self, callableObj, *args, **kwargs):
        Thread.__init__(self)
        self.callableObj = callableObj
        self.args = args
        self.kwargs = kwargs
        self.terminateEvent = None

    def onTerminate(self, method):
        self.terminateEvent = method

    def run(self):
        try:
            self.callableObj(*self.args, **self.kwargs)
        finally:
            # beware that this is called within the thread
            if self.terminateEvent is not None:
                self.terminateEvent()

def getMemberById(context, uid):
    """ exported for z2 dependency """
    if hasattr(context, 'portal_membership'):
        return context.portal_membership.getMemberById(uid)
    else:
        return None

def secureUnicode(unicode_content):
    """ make sure given unicode can be safely encoded in iso8859-15
    """
    string_ = unicode_content.encode('ISO-8859-15', 'replace')
    return string_.decode('ISO-8859-15')

def Utf8ToIso(value, codec='ISO-8859-15'):
    """ decode a str
    >>> Utf8ToIso(None)
    >>> Utf8ToIso('')
    ''
    >>> Utf8ToIso('donothing')
    'donothing'
    """
    if isinstance(value, str):
        uvalue = value.decode('utf-8', 'replace')
        return uvalue.encode(codec)
    else:
        return value

def linkifyMailBody(body, email_sub=r'<a href="mailto:\3">\3</a>'):
    """ replace mails and urls by links

    if mail_sub is given, it's used for replacement,
    so it can be set to link to an internal mail editor
    """
    changed = False
    linkificators = ((r'(<|^|\b|\(|\()(https|ftp|http)(://)([^ \b\n<>]*)(>|$|\b)?',
                      r'<a href="\2\3\4" target="_blank">\2\3\4</a>'),
                     (r'((?<=[\s])(<)?)([\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4})(>)?',
                      email_sub))

    for pattern, replacer in linkificators:
        try:
            body = re.sub(pattern, replacer, body)
        except:
            raise pattern

    return body

    # first we need to find already link parts to avoid to relink them
    http_links = r'(<a.*?>).*?(</a>)|(<img.*?>)'
    http_links = re.compile(http_links, re.MULTILINE and re.I)

    changes = []
    for pattern, replacer in linkificators:
        ignore_parts = []
        for match in http_links.finditer(body):
            ignore_parts.append((match.start(), match.end()))

        matcher = re.compile(pattern, re.MULTILINE and re.I)

        for match in matcher.finditer(body):
            start = match.start()
            end = match.end()
            # checking that we are not within a link already
            linkify = True
            for istart, iend in ignore_parts:
                if start >= istart and end <= iend:
                    linkify = False
                    break
            if linkify:
                changed = True
                text_to_link = body[start:end]
                linker = text_to_link
                if linker[0] == '<' and linker[-1] == '>':
                    linker = linker[1:-1]
                linked_text = replacer.replace('$1', linker)
                changes.append((text_to_link, linked_text))

    for original, changed in changes:
        body = body.replace(original, changed)

    return body


def answerSubject(subject, fwd=False):
    """ prepare reply subject """
    if not fwd:
        if subject.lower().startswith('re:'):
            return subject
        else:
            return 'Re: %s' % subject
    else:
        if subject.lower().startswith('fwd:'):
            return subject
        else:
            return 'Fwd: %s' % subject

def translate(context, msg):
    """ translate msg, used to isolate localizer use """
    if hasattr(context, 'Localizer'):
        translator = context.Localizer.default
        return translator.gettext(msg)
    else:
        return msg

def createDigest(msg):
    """ create a message digest """
    if msg is None:
        return None
    subs = ('Date', 'Subject', 'From', 'To', 'Cc', 'Message-ID')
    sub_keys = {}
    for sub in subs:
        if msg.getHeader(sub) != []:
            sub_keys[sub] = msg.getHeader(sub)

    all_values = str(sub_keys.values())
    return md5Hash(all_values)

def createDigestFromList(headers):
    """ create a message digest from given headers """
    subs = ('Date', 'Subject', 'From', 'To', 'Cc', 'Message-ID')
    sub_keys = {}
    for sub in subs:
        if sub in headers:
            sub_keys[sub] = headers[sub]

    all_values = str(sub_keys.values())
    return md5Hash(all_values)

def traverseToObject(root, path):
    """ transforms a path into an object

    XXX need to use regular travsersal here later, in z3
    """
    path = path.split('/')
    if len(path) == 0:
        return None
    while len(path) > 0 and path[0] != root.id:
        del path[0]
    if len(path) == 0:
        return None
    # starting at root
    del path[0]
    subject = root
    for element in path:
        if hasattr(subject, element):
            subject = getattr(subject, element)
        else:
            return None
    return subject

def parseRefs(refs):
    """ transforms a reference string into a ref list """
    re_script = r'<\S*>'
    result = re.findall(re_script, refs.strip())
    return [ref.strip() for ref in result]

def shrinkHtml(text, remove_quoted=True):
    """ shrink mail body rendered in HTML

    will remove empty lines and optionnaly,
    all lines starting with >
    """
    shrinked = []
    text = text.replace('<br/>', '\n')
    text = text.replace('<br>', '\n')
    text = text.split('\n')
    i = 0
    for line in text:
        sline = line.strip()

        condition1 = (sline == '' and ((i < len(text) - 2 and
                      text[i+1].strip() == '') or i == len(text) - 1))

        condition2 = ((sline.startswith('>') or sline.startswith('&gt;')) and
                       remove_quoted)

        condition3 = (sline.endswith(':') and i < len(text) - 2
                      and (text[i+1].strip().startswith('>') or
                           text[i+1].strip().startswith('&gt;'))
                     )

        if condition1 or condition2 or condition3:
            shrinked.append('<span class="shrinkable not_hidden_part">%s<br/></span>' % line)
        else:
            shrinked.append('%s<br/>' % line)
        i += 1

    return ''.join(shrinked)

def divideMailBody(text, level=0):
    """ returns a tree of divs, according to quoting """
    text = text.replace('&gt;', '>')
    text = text.replace('&lt;', '<')
    text = text.replace('<br/>', '\n')
    text = text.replace('<br>', '\n')
    text = text.split('\n')
    blocs = []
    i = 0
    id_seed = 'topicBloc'
    while i < len(text):

        if text[i].startswith('>'):
            end_quote = i + 1
            while end_quote < len(text):
                if not text[end_quote].startswith('>'):
                    break
                end_quote += 1
            # we have a bloc
            bloc = text[i:end_quote]
            bloc = [line[1:] for line in bloc]
            bloc = '<br/>'.join(bloc)

            # recursive call
            bloc = divideMailBody(bloc, level+1)
            id = '%s%d%d' %(id_seed, level, i)
            if level == 0:
                retractor = ('<div class="topicRetractor" '
                             'onmouseover="setCursor(this)" '
                             'onclick="toggleElementVisibility(\'%s\')"><img '
                             'src="cpsma_retract_topic.png"/></div>' % id)

                blocs.append('<div class="bloc_%s">%s<div id="%s">%s</div></div>' % \
                         (str(level), retractor, id, bloc))
            else:
                blocs.append('<div class="bloc_%s"><div id="%s">%s</div></div>' % \
                         (str(level), id, bloc))

            i = end_quote
        else:
            blocs.append(text[i])
        i += 1

    return '<br/>'.join(blocs)

def getAuthenticatedMember(context):
    if hasattr(context, 'portal_membership'):
        return context.portal_membership.getAuthenticatedMember()
    else:
        return None

def getPortalLang(context):
    if hasattr(context, 'Localizer'):
        return context.Localizer.get_selected_language()
    else:
        return 'en'


