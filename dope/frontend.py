from flask import Blueprint, redirect, url_for, render_template
from flask_wtf import Form
from wtforms.fields import SubmitField
from wtforms.validators import Required
from flask_wtf.file import FileField

from .auth import Auth, HTTPBasicAuth, ConfPasswordValidator


class UploadForm(Form):
    file = FileField(u'File to upload', validators=[Required()])
    upload = SubmitField(u'Upload file')


auth = Auth()
auth.add_method(HTTPBasicAuth(ConfPasswordValidator('FRONTEND_PASSWORD')))

frontend = Blueprint('frontend', __name__)


@frontend.route('/')
def index():
    return redirect(url_for('.upload_file'))


@frontend.route('/upload-file/', methods=('GET', 'POST'))
@auth.requires_login
def upload_file():
    form = UploadForm()

    if form.validate_on_submit():
        return 'ok'

    return render_template('upload-file.html', form=form)
