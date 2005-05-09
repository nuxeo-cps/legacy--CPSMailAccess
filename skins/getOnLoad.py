##parameters=
#$Id$
""" return the body onload attribute content
"""
request = container.REQUEST

if request.has_key('URL'):
    URL = container.REQUEST['URL']
    if URL is not None:
        if (URL.endswith('search_form') or URL.endswith('advanced_search_form') or \
                URL.endswith('searchMessage.html')):
            return 'highlightSearchTerm();setFocus();'

return 'setFocus();'
