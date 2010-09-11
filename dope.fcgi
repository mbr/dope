#!/usr/bin/env python
# coding=utf8

from flup.server.fcgi import WSGIServer
from dope import app

WSGIServer(app, bindAddress = app.config['FCGI_SOCKET']).run()
