#!/usr/bin/env python
# coding=utf8

from flaskext.wtf import Form, FileField, Required

class UploadForm(Form):
	uploaded_file = FileField(u'File to upload')
