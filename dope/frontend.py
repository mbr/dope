from flask import Blueprint, redirect, url_for, render_template

from .auth import Auth, HTTPBasicAuth, ConfPasswordValidator


auth = Auth()
auth.add_method(HTTPBasicAuth(ConfPasswordValidator('FRONTEND_PASSWORD')))

frontend = Blueprint('frontend', __name__)


@frontend.route('/')
def index():
    return redirect(url_for('.upload_file'))


@frontend.route('/upload-file/')
@auth.requires_login
def upload_file():
    return render_template('logobase.html')
