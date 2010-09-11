#!/usr/bin/env python
# coding=utf8

import uuid

from flask import Flask, render_template, request, redirect, url_for, abort
from werkzeug import secure_filename
import forms

from app import *
import model

storage = model.FileStorage(app.config['FILE_STORAGE'])

@app.route('/upload/', methods = ('GET', 'POST'))
def index():
	form = forms.UploadForm()
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
