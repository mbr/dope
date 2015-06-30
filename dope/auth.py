from functools import wraps

from flask import abort
from blinker import Namespace


signals = Namespace()
auth_needed = signals.signal('auth-needed')
new_auth_requested = signals.signal('new-auth-requested')


def requires_login(f):
    @wraps(f)
    def _(*args, **kwargs):
        for receiver, auth_object in auth_needed.send():
            # check if we have a login already
            if auth_object is not None:
                break
        else:
            # tell others we're missing a login (redirect to one)
            for receiver, response in new_auth_requested.send():
                if response is not None:
                    return response
            else:
                abort(403, 'Requested new auth, none received')
        return f(*args, **kwargs)
    return _
