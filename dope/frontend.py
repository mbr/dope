from flask import Blueprint

from .auth import requires_login


frontend = Blueprint('frontend', __name__)


@frontend.route('/')
@requires_login
def index():
    return 'hello'
