from flask import Blueprint

from .auth import requires_login, HTTPBasicAuth, ConfPasswordValidator


frontend = Blueprint('frontend', __name__)
frontend_auth = HTTPBasicAuth(ConfPasswordValidator('FRONTEND_PASSWORD'))
frontend_auth.activate()


@frontend.route('/')
@requires_login
def index():
    return 'hello'
