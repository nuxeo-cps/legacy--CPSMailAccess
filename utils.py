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
import string, re



_translation_table = string.maketrans(
    # XXX candidates: @°+=`|
    r""""'/\:; &ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöøùúûüýÿ""",
    r"""________AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuyy""")

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
    while seed + str(i) in container.objectIds():
        i +=1

    return makeId(seed + str(i))
