#!/usr/bin/env python
# coding=utf8

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flaskext.openid import OpenID

import model
import defaults
from views.frontend import frontend

def create_app(config_filename):
	app = Flask(__name__)
	app.config.from_object(defaults)
	app.config.from_pyfile(config_filename)

	# init db connection
	engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], encoding = 'utf8', echo = app.config['SQLALCHEMY_ECHO'])
	app.session = scoped_session(sessionmaker(bind = engine))

	@app.after_request
	def shutdown_session(response):
		app.session.remove()
		return response

	app.storage = model.FileStorage(app.config['FILE_STORAGE'])
	app.oid = frontend.oid
	app.oid.init_app(app)

	# load modules
	app.register_module(frontend)

	return app
