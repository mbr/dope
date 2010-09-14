#!/usr/bin/env python
# coding=utf8

from functools import wraps

import uuid

from flask import Flask, render_template, request, redirect, url_for, abort, g, session
from flaskext.openid import OpenID
from werkzeug import secure_filename
import forms

from app import *
import model

storage = model.FileStorage(app.config['FILE_STORAGE'])
oid = OpenID(app)

debug = app.logger.debug

def require_login(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		if not g.user:
			# need to login first
			return redirect(url_for('login', next = request.url))
		return f(*args, **kwargs)

	return wrapper

@app.before_request
def lookup_current_user():
	g.user = None
	if 'userid' in session:
		g.user = model.User.query.filter_by(id = session['userid'])

	debug('user: %s', g.user)

@app.route('/login/', methods = ('GET', 'POST'))
@oid.loginhandler
def login():
	if g.user is not None:
		# if the user is logged in already, redirect to next url
		g.user = None
		debug('logged user out')

	form = forms.OpenIDLoginForm(request.form, next = oid.get_next_url())
	if request.method == 'POST':
		return oid.try_login(form.openid.data)

	return render_template('openidlogin.xhtml', form = form, error = oid.fetch_error())

@oid.after_login
def create_or_login(resp):
	session['openid'] = resp.identity_url

	# look up if open id exists
	o = model.OpenID.query.filter_by(id = resp.identity_url).first()
	if not o:
		# create a new user
		u = model.User()
		o = model.OpenID(resp.identity_url, u)
		db.session.add(u)
		db.session.add(o)
		db.session.commit()

		debug('created new user: %s', u)
	else:
		u = o.user

	session['userid'] = u.id

	# redirect user where he wanted to go in the first place
	return redirect(oid.get_next_url())

@app.route('/upload/', methods = ('GET', 'POST'))
def index():
	form = forms.UploadForm(request.form)
	if form.validate_on_submit():
		# create new file object
		f = model.File(storage, form.uploaded_file.file)

		db.session.add(f)
		db.session.commit()

		app.logger.debug('added: %s', f)

		return render_template('success.xhtml', f = f)

	form_markup = render_template('upload_form.xhtml', form = form)
	return render_template('upload.xhtml', title = 'Upload file.', form = form_markup)

@app.route('/download/<public_id>')
def download(public_id):
	try:
		f = model.File.query.filter_by(public_id = uuid.UUID(public_id)).first_or_404()
	except ValueError:
		abort(404)

	resp = storage.send(f.storage_id, f.filename, f.content_type)
	resp.content_length = f.size

	return resp

if __name__ == '__main__':
	app.run(debug = app.config['DEBUG'], use_debugger = app.config['DEBUG'], use_reloader = app.config['DEBUG'])
