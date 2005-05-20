##parameters=user,light=1
# $Id$
""" calls zasync if available or call direct synchro
    then redirect to INBOX if it already exists
    or to root box

    XXXX needs to be put in mailtool class
"""
# XXX executed as root when asynced,
# need to change mails owner when they are created
box_name = 'box_%s' % user
req = context.REQUEST
res = True

if hasattr(context, 'asynchronous_call_manager'):
    # XXX need to get feedback in case of failures
    bckgrd = True
    acm = context.asynchronous_call_manager
    root = container.portal_url.getPortalPath()
    root = root.replace('/', '.')
    if root[0] == '.':
        root = root[1:]
    acm.putCall('zope_exec', '/', {},
                'python:home.%s.portal_webmail.background("%s", %s)' \
                % (root, box_name, str(light)), {})
else:
    bckgrd = False
    try:
        container.background(box_name, light)
    # except ConnectionError: this will be available when code is put in
    # mailtoool class
    except:
        res = False

if req is not None:
    root = container.portal_url()
    if res:
        if bckgrd:
            psm = 'cps_synchronizing'
        else:
            psm = None
    else:
        psm = 'cpsma_failed_synchro'

    box = container.portal_webmail[box_name]
    if hasattr(box, 'INBOX'):
        page = '%s/portal_webmail/%s/INBOX' %(root, box_name)
    else:
        page = '%s/portal_webmail/%s' %(root, box_name)

    if psm is not None:
        req.RESPONSE.redirect('%s/view?msm=%s'  % (page, psm))
    else:
        req.RESPONSE.redirect('%s/view'  % page)
