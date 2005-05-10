##parameters=user,light=True
# $Id$
""" calls zasync if available or call direct synchro """
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
    if req is not None:
        root = container.portal_url()
        psm = 'cps_synchronizing'
        req.RESPONSE.redirect('%s/portal_webmail/%s/view?portal_status_message=%s' \
                               % (root, box_name, psm))
else:
    container.background(box_name, light)
