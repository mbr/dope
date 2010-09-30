#!/usr/bin/env python
# coding=utf8

# This is an example of how to run dope (or any other WSGI app) in CherryPy.
# Running it will start dope at the document root, and the server on port 80.
#
# Assuming a virtual environment in which cherrypy is installed, this would be
# the way to run it.

from dope import app
import cherrypy
import drop_privileges

# set this to whatever user you want to run dope as. must have read access to the code/templates/etc.
# and write to the openid and other subfolders
run_as_user = 'nobody'
run_as_group = 'nogroup'

# graft to tree root
cherrypy.tree.graft(app)

# configure
cherrypy.config.update({
	'server.socket_port': 80,
})

# drop priviledges
cherrypy.process.plugins.DropPrivileges(cherrypy.engine, uid = run_as_user, gid = run_as_group).subscribe()
