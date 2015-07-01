# note: this auth module is slightly experimental in and intended to spun out
#       as a standalone component. just in case you were wondering why it
#       seems slightly overengineered for simple http basic auth...

from functools import wraps

from flask import abort, Response, request, current_app
from passlib.utils import consteq


class Auth(object):
    def __init__(self, methods=None):
        self.methods = methods or []

    def add_method(self, method):
        self.methods.append(method)

    def destroy(self):
        pass  # nothing persisted, nothing to destroy

    def persist(self, auth):
        pass  # do not persist, require new login each time

    def requires_login(self, f):
        @wraps(f)
        def _(*args, **kwargs):
            for method in self.methods:
                auth = method.get_current_auth()
                if auth:
                    self.persist(auth)
                    break
            else:
                # no auth found, request one
                for method in self.methods:
                    response = method.request_new_auth()

                    if response:
                        return response
                else:
                    abort(403, 'Requested new auth, none received')

            # all good, we're authed
            return f(*args, **kwargs)
        return _


class AuthMethod(object):
    def get_current_auth(self):
        pass

    def request_new_auth(self):
        pass


class AuthBackend(object):
    def verify(self, creds):
        pass


class Credentials(object):
    pass


class UserPasswordCredentials(Credentials):
    def __init__(self, username, password):
        self.username = username
        self.password = password


class ConfPasswordValidator(AuthBackend):
    def __init__(self, varname):
        self.varname = varname

    def verify(self, creds):
        if consteq(creds.password, current_app.config[self.varname]):
            return creds.username


class HTTPBasicAuth(AuthMethod):
    def __init__(self, validator, msg='Please login.', realm='Login required'):
        self.validator = validator
        self.msg = msg
        self.realm = realm

    def get_current_auth(self):
        # we're checking if credentials have been suppied
        auth = request.authorization

        if auth:
            creds = UserPasswordCredentials(
                auth.username, auth.password
            )
            return self.validator.verify(creds)

    def request_new_auth(self):
        return Response(
            'Please login', 401,
            {'WWW-Authenticate': 'Basic realm="Login required"'}
        )
