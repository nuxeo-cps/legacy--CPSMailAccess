##parameters=box_name, light=True
# $Id$
box = getattr(container.portal_webmail, box_name, None)
box.synchronize(no_log=True, light=light)
