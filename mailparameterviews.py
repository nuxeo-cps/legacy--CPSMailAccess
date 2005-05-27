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
from Products.Five import BrowserView


class MailParametersView(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)


    def _getParameters(self):
        """ returns a list of parameters
        """
        ob = self.context
        return ob.getConnectionParams()

    def renderParameters(self):
        """ renders parameters
        """
        params = self._getParameters()
        form = '<dl>'
        for param in params.keys():
            form += '<dt>%s</dt><dd>%s</dd>' %(param, params[param])
        form += '</dl>'
        return form

    def _computeRequest(self, params):
        """ creates params from request """
        if self.request is not None and hasattr(self.request, 'form'):
            form = self.request.form
            for element in form.keys():
                params[element] = form[element]

        if params.has_key('submit'):
            del params['submit']

        # XXX need to check each parameters
        # to avoid resync if not needed
        combined_params = {}
        for key in params.keys():
            if not key.startswith('secu_'):
                if params.has_key('secu_%s' % key):
                    value = params['secu_%s' % key]
                    # for checkboxes
                    if not isinstance(value, int):
                        if value == 'on':
                            # parameter becomes common to all boxes
                            value = 1
                        else:
                            value = 0
                    combined_params[key] = (params[key], value)
                else:
                    combined_params[key] = (params[key], 1)

        return combined_params

    def setParameters(self, params={}):
        """ sets given parameters

        when mailtool parameters are changed,
        and parameter is portal-wide, it's a passive change made
        to all existing mailboxes, wich means, they will upgrade
        their own parameters in the next parameter use
        """
        params = self._computeRequest(params)
        self.context.setParameters(params, False)
        if self.request is not None:
            self.request.response.redirect('configure.html')

class MailToolParametersView(MailParametersView):

    def renderParametersForm(self):
        """ returns a form with parameters

        XXXX see for zope 3 schema/widget use here
        """
        if self.request is not None:
            if self.request.has_key('submit'):
                self.setParameters(self.request)

        params = self._getParameters()
        rendered_params = []

        for param in params.keys():
            if param == 'uid':
                continue
            value, secu = params[param]

            rendered_param = {}
            rendered_param['name'] = param
            rendered_param['value'] = value
            rendered_param['secu'] = secu

            if param == 'password' and not value.startswith('${'):
                rendered_param['type'] = 'password'
            elif param == 'signature':
                rendered_param['type'] = 'list'
            else:
                rendered_param['type'] = 'text'

            if isinstance(value, int):
                rendered_param['ptype'] = 'int'
            elif isinstance(value, list):
                rendered_param['ptype'] = 'list'
                value = ','.join(value)
            else:
                rendered_param['ptype'] = 'string'

            rendered_params.append(rendered_param)

        rendered_params.sort()
        return rendered_params

class MailBoxParametersView(MailParametersView):

    def _getParameters(self):
        """ returns a list of parameters  """
        ob = self.context
        return ob.getConnectionParams(remove_security=False)

    def renderParametersForm(self):
        """ returns a form with parameters

        XXXX see for zope 3 schema/widget use here
        """
        if self.request is not None:
            if self.request.has_key('submit'):
                self.setParameters(self.request)

        params = self._getParameters()
        rendered_params = []

        for param  in params.keys():
            value, secu = params[param]

            if param == 'uid' or secu == 0:
                continue

            rendered_param = {}
            rendered_param['name'] = param
            rendered_param['value'] = value
            if param == 'password' and not value.startswith('${'):
                rendered_param['type'] = 'password'
            elif param == 'signature':
                rendered_param['type'] = 'list'
            else:
                rendered_param['type'] = 'text'

            if isinstance(value, int):
                rendered_param['ptype'] = 'int'
            elif isinstance(value, list):
                rendered_param['ptype'] = 'list'
                value = ','.join(value)
            else:
                rendered_param['ptype'] = 'string'

            rendered_params.append(rendered_param)

        rendered_params.sort()
        return rendered_params

    def getUserName(self):
       """ retrieves user name """
       return self._getParameters()['uid']

    def clearMailCatalog(self):
        """ clear catalog """
        box = self.context
        box.clearMailCatalog()

        if self.request is not None:
            psm = 'Catalog cleared.'
            self.request.response.redirect('configure.html?msm=%s' % psm)

    def reindexMailCatalog(self):
        """ calls the catalog indexation """
        box = self.context
        box.reindexMailCatalog()

        if self.request is not None:
            psm = 'All mails are indexed'
            self.request.response.redirect('configure.html?msm=%s' % psm)

    def reconnect(self):
        """ calls the box relog """
        box = self.context
        box.reconnect()

        if self.request is not None:
            psm = 'cpsma_relogged'
            self.request.response.redirect('configure.html?msm=%s' % psm)

    def clearMailBodies(self):
        """ calls the box clearer """
        box = self.context
        box.clearMailBodies()

        if self.request is not None:
            psm = 'cpsma_cleared'
            self.request.response.redirect('configure.html?msm=%s' % psm)


class MailBoxFiltersView(BrowserView):

    def getFilterCount(self):
        mailbox = self.context
        filters = mailbox.getFilters()
        return len(filters.getFilters())

    def _render(self, item):
        render_item = {}

        if item['subject'] == 'From':
            render_item['subject'] = 'Sender'
        else:
            render_item['subject'] = item['subject']

        render_item['action_param'] = item['action_param']
        render_item['value'] = item['value']

        cond = item['condition']

        if cond == 1:
            render_item['condition']  = 'contains'
        elif cond == 2:
            render_item['condition']  = 'does not contains'
        elif cond == 3:
            render_item['condition']  = 'begins with'
        elif cond == 4:
            render_item['condition']  = 'ends with'
        elif cond == 5:
            render_item['condition']  = 'is'
        elif cond == 6:
            render_item['condition']  = 'is not'
        else:
            render_item['condition'] = '? : %s' % str(cond)

        action = item['action']

        if action == 1:
            render_item['action']  = 'move to'
        elif action == 2:
            render_item['action']  = 'copy to'
        elif action == 3:
            render_item['action']  = 'label with'
        elif action == 4:
            render_item['action']  = 'set junk status'
        else:
            render_item['action'] = '? : %s' % str(action)

        return render_item

    def renderFilters(self):
        """ renders filter list

        Replaces values by human readable values
        """
        mailbox = self.context
        filters = mailbox.getFilters().getFilters()
        return map(self._render, filters)

    def removeFilter(self, index):
        """ removes a filter given its index"""
        mailbox = self.context
        filters = mailbox.getFilters()
        filters.deleteFilter(index)

        if self.request is not None:
            self.request.response.redirect('filters.html')

    def addFilter(self, subject, condition, value, action, action_param=None):
        """ adds a filter given its values """
        mailbox = self.context
        filters = mailbox.getFilters()

        # controling input
        if action != 4 and action_param.strip() == '':
            psm = 'Need an action param'
        else:
            filters.addFilter(subject, condition, value, action, action_param)
            psm = None

        if self.request is not None:
            if psm is None:
                self.request.response.redirect('filters.html')
            else:
                self.request.response.redirect(
                    'filters.html?msm=%s' % psm)

    def moveFilter(self, index, direction):
        """ moves a filter given a direction

                0 : up
                1: down
        """
        mailbox = self.context
        filters = mailbox.getFilters()
        filters.moveFilter(index, direction)
        if self.request is not None:
            self.request.response.redirect('filters.html')

