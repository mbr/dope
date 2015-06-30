# note: this auth module is slightly experimental in and intended to spun out
#       as a standalone component. just in case you were wondering why it
#       seems slightly overengineered for simple http basic auth...

from functools import wraps

from flask import abort, Response, request, current_app
from blinker import Namespace
from passlib.utils import consteq


signals = Namespace()
auth_needed = signals.signal('auth-needed')
new_auth_requested = signals.signal('new-auth-requested')


def requires_login(f):
    @wraps(f)
    def _(*args, **kwargs):
        for receiver, auth_object in auth_needed.send(request.endpoint):
            # check if we have a login already
            if auth_object is not None:
                break
        else:
            # tell others we're missing a login (redirect to one)
            for receiver, response in\
                    new_auth_requested.send(request.endpoint):
                if response is not None:
                    return response
            else:
                abort(403, 'Requested new auth, none received')
        return f(*args, **kwargs)
    return _


class Auth(object):
    def activate(self):
        auth_needed.connect(self.on_auth_needed)
        new_auth_requested.connect(self.on_new_auth_requested)

    def on_auth_needed(self, endpoint):
        pass

    def on_new_auth_requested(self, endpoint):
        pass


class Credentials(object):
    pass


class UserPasswordCredentials(Credentials):
    def __init__(self, username, password):
        self.username = username
        self.password = password


class CredentialValidator(object):
    def verify(self, creds):
        pass


class ConfPasswordValidator(CredentialValidator):
    def __init__(self, varname):
        self.varname = varname

    def verify(self, creds):
        if consteq(creds.password, current_app.config[self.varname]):
            return creds.username


class HTTPBasicAuth(Auth):
    def __init__(self, validator, msg='Please login.', realm='Login required'):
        self.validator = validator
        self.msg = msg
        self.realm = realm

    def on_auth_needed(self, endpoint):
        # we're checking if credentials have been suppied
        auth = request.authorization

        if auth:
            creds = UserPasswordCredentials(
                auth.username, auth.password
            )
            return self.validator.verify(creds)

    def on_new_auth_requested(self, endpoint):
        return Response(
            'Please login', 401,
            {'WWW-Authenticate': 'Basic realm="Login required"'}
        )
