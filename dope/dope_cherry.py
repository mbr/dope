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

# graft to tree root
cherrypy.tree.graft(app)

# configure
cherrypy.config.update({
	'server.socket_port': 80,
	'server.socket_host': '0.0.0.0',
	'server.max_request_body_size': 0, # unlimited
	'run_as_user': 'nobody',
	'run_as_group': 'nogroup',
})

# drop priviledges
cherrypy.process.plugins.DropPrivileges(cherrypy.engine, uid = cherrypy.config['run_as_user'], gid = cherrypy.config['run_as_group']).subscribe()