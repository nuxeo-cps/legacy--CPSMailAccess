## Script (Python) "background_synchro"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=user,light=True
##title=
##
# $Id$
""" calls zasync if available or call direct synchro """
box_name = 'box_%s' % user

if hasattr(context, 'asynchronous_call_manager'):
    acm = context.asynchronous_call_manager
    light = test(light, 'True', 'False')
    acm.putCall('zope_exec', '/', {},
                'python:home.cps.portal_webmail.background("%s", %s)' \
                % (box_name, light), {})
else:
    box = getattr(container.portal_webmail, box_name, None)
    box.synchronize(no_log=True, light=light)

req = context.REQUEST
if req is not None:
    req.RESPONSE.redirect('portal_webmail/%s/INBOX/view' % box_name)
    return 'done'
else:
    return 'called for %s '  % user