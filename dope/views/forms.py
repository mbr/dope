#!/usr/bin/env python
# coding=utf8

from flask import current_app
from flaskext.wtf import Form, FileField, Required, TextField, HiddenField, QuerySelectField, SelectMultipleField, ListWidget, CheckboxInput
from .. import model

class UploadForm(Form):
	uploaded_file = FileField(u'File to upload')

class OpenIDLoginForm(Form):
	openid = TextField(u'Your OpenID')
	next = HiddenField()

class SelectUser(Form):
	user = QuerySelectField(u'User', query_factory = lambda: current_app.session.query(model.User).all())

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

def create_permissions_form(*args, **kwargs):
	class PermissionsForm(Form):
		groups = MultiCheckboxField(u'Groups', coerce=int)

	form = PermissionsForm(*args, **kwargs)
	form.groups.choices = [(group.id, str(group)) for group in current_app.session.query(model.Group).query.all() if group.name not in ("anonymous", "registered")]

	return form
