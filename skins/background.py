##parameters=box_name, light=True
# $Id$
root = container.portal_url()
resp = context.REQUEST.RESPONSE
light = test(light, '1', '0')
resp.redirect('%s/portal_webmail/%s/synchronize.html?light=%s' %(root, box_name, light))

