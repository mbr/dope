#!/usr/bin/env python
# coding=utf8

from flaskext.wtf import Form, FileField, Required, TextField, HiddenField

class UploadForm(Form):
	uploaded_file = FileField(u'File to upload')

class OpenIDLoginForm(Form):
	openid = TextField(u'Your OpenID')
	next = HiddenField()
