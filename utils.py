# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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
""" a few utilities
"""
import string, re, md5
from email.Header import decode_header, make_header
from exceptions import UnicodeDecodeError
from zope.app.datetimeutils import DateTimeParser, SyntaxError as ZSyntaxError
from datetime import datetime
from time import strftime
from Acquisition import aq_get

_translation_table = string.maketrans(
    # XXX candidates: @°+=`|
    '"' r"""'/\:; &ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöøùúûüýÿ""",
    '_' r"""_______AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuyy""")

_ok_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_."


def makeId(s, lower=0):
    "Make id from string"
    id = s.translate(_translation_table)
    id = id.replace('Æ', 'AE')
    id = id.replace('æ', 'ae')
    id = id.replace('Œ', 'OE')
    id = id.replace('œ', 'oe')
    id = id.replace('ß', 'ss')
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

def md5Hash(string):
    """ returns a md5 key
    """
    m = md5.new()
    m.update(string)
    return m.hexdigest()

def decodeHeader(header):
    """ decodes a mail header
    """
    # see here if this encoding is ok
    try:
        decoded_header = decode_header(header)
        hu = make_header(decoded_header)
        hu = hu.__unicode__()

    #except UnicodeDecodeError, LookupError:
    #    hu = header

    ### need to find wich LookupError is
    except:
        hu = header
    return hu


def parseDateString(date_string):
    """ parses a string to render a date
        if no result, renders 1 jan 70
    >>> parseDateString('Wed, 29 Dec 2004 21:42:19 +0100')
    datetime.datetime(2004, 12, 29, 21, 42, 19)
    >>> parseDateString('Wed, 29 Dec 2004')
    datetime.datetime(2004, 12, 29, 0, 0)
    >>> parseDateString('hahahaha')
    datetime.datetime(1970, 1, 1, 0, 0)
    """
    parser= DateTimeParser()
    try:
        result = parser.parse(date_string)
        result = datetime(result[0], result[1], result[2],
            result[3], result[4], result[5])
    except ZSyntaxError:
        result = datetime(1970,1,1)

    return result

def localizeDateString(date_string, format=0):
    """ normalizes renders a localized date string
    XXXtodo : localize
    >>> localizeDateString('Wed, 29 Dec 2004 21:42:19 +0100')
    'Wed 29/12/04 21:42'
    >>> localizeDateString('Wed, 29 Dec 2004 21:42:19 +0100', 1)
    '21:42'
    >>> localizeDateString('Wed, 29 Dec 2004 21:42:19 +0100', 2)
    '29/12'
    >>> localizeDateString('Wed, 29 Dec 2004 21:42:19 +0100', 3)
    '29/12/04'
    """
    date = parseDateString(date_string)
    if format == 1:
        return date.strftime('%H:%M')
    elif format == 2:
        return date.strftime('%d/%m')
    elif format == 3:
        return date.strftime('%d/%m/%y')
    else:
        return date.strftime('%a %d/%m/%y %H:%M')

def isToday(date_string):
    """ tells if the given string represents today's date
    """
    date = parseDateString(date_string)
    today = date.now()
    return date.year == today.year and date.month ==today.month\
     and date.day == today.day

def truncateString(string, font_size, max_size):
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
    if len(string) * font_size > max_size:
        sub_max = max_size - (3*font_size)
        if sub_max<=0:
            return '...'
        sub_max = int(sub_max/ font_size)
        return string[:sub_max]+'...'
    else:
        return string

def mimetype_to_icon_name(mimetype):
    """ transforms a mimetype to an icon filename
        used for attached files
    >>> mimetype_to_icon_name('image/gif')
    'image_gif.png'
    >>> mimetype_to_icon_name('')
    'unknown.png'
    """
    if mimetype.strip() == '':
        return 'unknown.png'
    return mimetype.replace('/', '_')+'.png'

def _isinstance(ob, cls):
    try:
        return isinstance(ob, cls)
    except TypeError:
        # In python 2.1 isinstance() raises TypeError
        # instead of returning 0 for ExtensionClasses.
        return 0

def getFolder(mailbox, folder_name):
    current = mailbox
    path = folder_name.split('.')
    for element in path:
        if not hasattr(current, element):
            return None
        current = getattr(current, element)
    return current


def getCurrentDateStr():
    """ gets current date
    """
    date = datetime(1970, 1, 1)
    now = date.now()
    return now.strftime('%a %d/%m/%y %H:%M')

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
