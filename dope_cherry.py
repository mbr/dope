#!/usr/bin/env python
# coding=utf8

# This is an example of how to run dope (or any other WSGI app) in CherryPy.
# Running it will start dope at the document root, and the server on port 80.
#
# Assuming a virtual environment in which cherrypy is installed, this would be
# the way to run it:
#
# $ /path/to/virtualenv/bin/python /path/to/virtualenv/bin/cherryd -i dope_cherry

from dope import app
import cherrypy
import drop_privileges

# graft to tree root
cherrypy.tree.graft(app)

# configure
cherrypy.config.update({
	'server.socket_port': 80,
	'run_as_user': 'nobody',
	'run_as_group': 'nogroup',
})

cherrypy.config.update('dope_cherry.cfg')

# drop priviledges
cherrypy.process.plugins.DropPrivileges(cherrypy.engine, uid = cherrypy.config['run_as_user'], gid = cherrypy.config['run_as_group']).subscribe()
