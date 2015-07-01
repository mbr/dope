from flask import Blueprint

from .auth import Auth, HTTPBasicAuth, ConfPasswordValidator


auth = Auth()
auth.add_method(HTTPBasicAuth(ConfPasswordValidator('FRONTEND_PASSWORD')))

frontend = Blueprint('frontend', __name__)


@frontend.route('/')
@auth.requires_login
def index():
    return 'hello'
