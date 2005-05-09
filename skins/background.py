## Script (Python) "background"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=box_name, light=True
##title=
##
# $Id$
box = getattr(container.portal_webmail, box_name, None)
box.synchronize(no_log=True, light=light)
