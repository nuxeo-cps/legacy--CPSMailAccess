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
"""
     MailFiltering knows how to do some actions on MailMessage
     given some filter rules. a filter rule is a triple :

         subject / condition / value / action / action parameter (optional)

     filters are ordonnated

     actions :

         ° 1 : move to a specified folder
         ° 2 : copy to a specified folder
         ° 3 : label the message
         ° 4 : set junk status

    subjects :

         ° subject
         ° sender
         ° date
         ° To
         ° Cc
         ° To or Cc

    conditions :

         ° 1: contains
         ° 2: does not contains
         ° 3: begin with
         ° 4: ends with
         ° 5: is
         ° 6: isn't

    MailFiltering knows also how to deal with mailboxes
"""
from UserList import UserList

# zope 2 persistent classes
from Globals import Persistent
from ZODB.PersistentList import PersistentList

# zope 3 persistent classes
# can be used (same interface when switching to zope 3)
#from persistent import Persistent
#from persistent.list import PersistentList

from zope.interface import implements

from utils import getFolder, extractMailParts, decodeHeader
from interfaces import IMailFilteringBackEnd

class NormalBackEnd(UserList):
    """
    >>> f = NormalBackEnd()
    >>> IMailFilteringBackEnd.providedBy(f)
    True
    """
    implements(IMailFilteringBackEnd)

    def countFilters(self):
        return len(self)

    def appendFilter(self, filter_):
        self.append(filter_)

    def deleteFilter(self, index):
        del self[index]

    def moveFilter(self, index, direction):
        """ moves a filter given a direction

        Done if possible,
            0 : up
            1: down
        """
        if direction == 1:
            if index < self.countFilters() - 1 and index >= 0:
                switch = self[index+1]
                self[index+1] = self[index]
                self[index] = switch
        else:
            if index > 0  and index < self.countFilters():
                switch = self[index-1]
                self[index-1] = self[index]
                self[index] = switch

class MailFiltering:

    def __init__(self, backend=None):
        if backend is None:
            self._filters = NormalBackEnd()
        else:
            self._filters = backend

    def _listFilters(self):
        return self._filters

    def _countFilters(self):
        return self._filters.countFilters()

    def _appendFilter(self, filter_):
        self._filters.appendFilter(filter_)

    def _deleteFilter(self, index):
        self._filters.deleteFilter(index)

    def _findElement(self, subject, condition, value):
        """ finds an entry """
        i = 0
        for element in self._listFilters():
            if (element['subject'] == subject and
                element['condition'] == condition and
                element['value'] == value):
                return i
            else:
                i += 1
        return -1

    def getFilterCount(self):
        """ retrieve filter count """
        return self._countFilters()

    def getFilters(self):
        """ retrieve filter count """
        return self._listFilters()

    def addFilter(self, subject, condition, value, action, action_param=None):
        """ adds a filter to the list """
        i = self._findElement(subject, condition, value)
        if i == -1:
            element = {}
            element['subject'] = subject
            element['condition'] = condition
            element['value'] = value
            element['action'] = action
            element['action_param'] = action_param
            self._appendFilter(element)

    def delFilter(self, subject, condition, value):
        """ deletes a filter from the list """
        i = self._findElement(subject, condition, value)
        if i != -1:
            self._deleteFilter(i)

    def deleteFilter(self, index):
        """ direct index deletion """
        self._deleteFilter(index)

    def _matchCondition(self, value, condition, condition_value):
        """ tests value with condition value

        condition possible values :
            ° 1: contains
            ° 2: does not contains
            ° 3: begin with
            ° 4: ends with
            ° 5: is
            ° 6: isn't
        """
        # if value is None
        # we consider it's ''
        if value is None:
            value = ''
        else:
            value = value.lower().strip()

        # XXX need to use message encoding here
        value = decodeHeader(value)
        if isinstance(value, str):
            value = value.decode('ISO-8859-15')

        condition_value = condition_value.lower().strip()
        if isinstance(condition_value, str):
            condition_value = condition_value.decode('ISO-8859-15')

        if condition == 1:
            return value.find(condition_value) != -1
        elif condition == 2:
            return value.find(condition_value) == -1
        elif condition == 3:
            return value.startswith(condition_value)
        elif condition == 4:
            return value.endswith(condition_value)
        elif condition == 5:
            if value == condition_value:
                return True
            values = extractMailParts(value)
            return condition_value in values
        elif condition == 6:
            return value != condition_value
        else:
            return False

    def _filterMatches(self, element, message):
        """ see if a message matches a given filter """
        header = element['subject']
        header_values = message.getHeader(header)
        if header_values == [] or header_values is None:
            return False

        # when mutli-value header, check for any
        condition = element['condition']
        condition_value = element['value']

        for header_value in header_values:
            if self._matchCondition(header_value, condition, condition_value):
                return True
        return False

    def _actionFilter(self, element, message):
        """ do an action on a message

         actions :
            ° 1 : move to a specified folder
            ° 2 : copy to a specified folder
            ° 3 : label the message
            ° 4 : set junk status

         return True if action has been done
        """
        action = element['action']
        if action in (1, 2):
            target_folder = element['action_param']
            current_folder = message.getMailFolder()
            if current_folder is not None:
                if current_folder.server_name != target_folder:
                    mailbox = current_folder.getMailBox()
                    ob_target_folder = getFolder(mailbox, target_folder)
                    if ob_target_folder is not None:
                        if action == 1:
                            current_folder.moveMessage(message.uid,
                                                       ob_target_folder)
                        else:
                            current_folder.copyMessage(message.uid,
                                                       ob_target_folder)
                    return True
        elif action == 3:
            # todo : labeling has to be done on server side too
            subject = message.getHeader('Subject')[0]
            label = element['action_param']
            new_subject = u'[%s] %s' %(label, subject)
            message.setHeader('Subject', new_subject)
            return True
        elif action == 4:
            message.junk = element['action_param']
            return True
        else:
            pass

        return False

    def filterMessage(self, message):
        """ apply an action """
        for element in self._listFilters():
            if self._filterMatches(element, message):
                if self._actionFilter(element, message):
                    break

    def moveFilter(self, index, direction):
        """ moves a filter given a direction

                0 : up
                1: down
        """
        self._filters.moveFilter(index, direction)


#
# persistent Zope backend
#
class ZODBMailBackEnd(PersistentList):
    """
    >>> f = ZODBMailBackEnd()
    >>> IMailFilteringBackEnd.providedBy(f)
    True
    """
    implements(IMailFilteringBackEnd)

    def countFilters(self):
        return len(self)

    def appendFilter(self, filter_):
        self.append(filter_)

    def deleteFilter(self, index):
        del self[index]

    def moveFilter(self, index, direction):
        """ moves a filter given a direction

        Done if possible,
            0 : up
            1: down
        """
        if direction == 1:
            if index < self.countFilters() - 1 and index >= 0:
                switch = self[index+1]
                self[index+1] = self[index]
                self[index] = switch
        else:
            if index > 0  and index < self.countFilters():
                switch = self[index-1]
                self[index-1] = self[index]
                self[index] = switch

class ZMailFiltering(MailFiltering, Persistent):

    def __init__(self):
        zodb_list = ZODBMailBackEnd()
        MailFiltering.__init__(self, zodb_list)
