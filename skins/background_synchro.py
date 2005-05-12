##parameters=user,light=True
# $Id$
""" calls zasync if available or call direct synchro
    then redirect to INBOX if it already exists
    or to root box
"""
box_name = 'box_%s' % user
req = context.REQUEST

if hasattr(context, 'asynchronous_call_manager'):
    acm = context.asynchronous_call_manager
    light = test(light, 'True', 'False')
    root = container.portal_url.getPortalPath()
    root = root.replace('/', '.')
    if root[0] == '.':
        root = root[1:]
    acm.putCall('zope_exec', '/', {},
                'python:home.%s.portal_webmail.background("%s", %s)' \
                % (root, box_name, light), {})
else:
    container.background(box_name, light)

if req is not None:
    root = container.portal_url()
    psm = 'cps_synchronizing'
    box = container.portal_webmail[box_name]

    if hasattr(box, 'INBOX'):
        page = '%s/portal_webmail/%s/INBOX' %(root, box_name)
    else:
        page = '%s/portal_webmail/%s' %(root, box_name)

    req.RESPONSE.redirect('%s/view?portal_status_message=%s'  % (page, psm))
