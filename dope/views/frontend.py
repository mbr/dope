#!/usr/bin/env python
# coding=utf8

from functools import wraps
import uuid

from flask import Module, Flask, render_template, request, redirect, url_for, abort, g, session, jsonify, request_finished, current_app
from flaskext.openid import OpenID
import werkzeug
from werkzeug import secure_filename

import forms
from .. import model

from sqlalchemy.orm.exc import NoResultFound

frontend = Module(__name__)

# FIXME: this needs to become per-instance
oid = OpenID()

def debug(*args, **kwargs):
    current_app.logger.debug(*args, **kwargs)

def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not g.user:
            # need to login first
            return redirect(url_for('login', next = request.url))
        return f(*args, **kwargs)

    return wrapper


def require_permission(verb, obj = None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # check if there is permission to do action_name
            user = getattr(g, 'user', None)
            if not model.user_has_permission(user, verb, obj):
                # check if a login would redeem our situation
                registered = current_app.session.query(model.Group).filter_by(name = "registered").one()
                if registered.may(verb, obj):
                    return redirect(url_for('login', next = request.url))
                debug('login futile: %s on %s',verb,obj)
                raise Exception("Permission denied")
            return f(*args, **kwargs)
        return wrapper
    return decorator


@request_finished.connect_via(frontend)
def add_nocache_headers(sender, response):
    response.headers.add('Cache-Control','no-cache, no-store, max-age=0, must-revalidate')


@frontend.before_request
def lookup_current_user():
    g.user = None
    g.user_has_permission = model.user_has_permission
    if 'userid' in session:
        g.user = current_app.session.query(model.User).filter_by(id = session['userid']).one()

    debug('user: %s', g.user)


@frontend.before_request
def persist_session():
    if current_app.config['PERSIST_SESSION']:
        session.permanent = True


@frontend.route('/login/', methods = ('GET', 'POST'))
@oid.loginhandler
def login():
    if g.user is not None:
        # if the user is logged in already, redirect to next url
        g.user = None
        debug('logged user out')

    # if the user clicked on login from the index page,
    # we want to redirect him directly to the upload page
    next_url = oid.get_next_url()
    if request.url_root == next_url: next_url = url_for('upload')

    form = forms.OpenIDLoginForm(request.form, next = next_url)
    if request.method == 'POST':
        return oid.try_login(form.openid.data)
    elif 'openid' in request.args:
        return oid.try_login(request.args['openid'])

    return render_template('openidlogin.xhtml', form = form, error = oid.fetch_error(), title = 'Please login')


@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url

    # look up if open id exists
    o = current_app.session.query(model.OpenID).filter_by(id = resp.identity_url).first()
    if not o:
        # create a new user
        u = model.create_new_user(resp.identity_url)
    else:
        u = o.user

    session['userid'] = u.id

    # redirect user where he wanted to go in the first place
    return redirect(oid.get_next_url())


@frontend.route('/single_upload/', methods = ('GET', 'POST'))
@require_permission('upload_file')
def single_upload():
    form = forms.UploadForm(request.form)
    if form.validate_on_submit():
        try:
            # create new file object
            f = model.File(current_app.storage, form.uploaded_file.file)

            current_app.session.add(f)
            current_app.session.commit()

            debug('added: %s', f)
        finally:
            # close the uploaded file handle - otherwise we will
            # "leak" a file on the filesystem that is the size of
            # the uploaded file
            form.uploaded_file.file.close()

        return render_template('success.xhtml', f = f)

    form_markup = render_template('single_upload_form.xhtml', form = form)
    return render_template('single_upload.xhtml', title = 'Upload file.', form = form_markup)


@frontend.route('/upload')
@require_permission('upload_file')
def upload():
    return render_template('upload.xhtml', title = 'Upload files.')


@frontend.route('/upload/submit_file/', methods = ('GET', 'POST'))
@require_permission('upload_file')
def upload_send_file():
    incoming = request.files['file']
    try:
        # create new file object
        f = model.File(current_app.storage, incoming)

        current_app.session.add(f)
        current_app.session.commit()

        return jsonify(file_url = f.absolute_download_url, file_name = f.filename)
    finally:
        incoming.close()


@frontend.route('/download/<public_id>')
@frontend.route('/download/<public_id>/<as_filename>')
@require_permission('download_file')
def download(public_id, as_filename = None):
    try:
        f = current_app.session.query(model.File).filter_by(public_id = uuid.UUID(public_id)).one()

        # redirect so we get a proper filename when downloading
        if current_app.config['SMART_FILENAME_REDIRECT'] and not as_filename: return redirect(url_for('download', public_id = public_id, as_filename = f.filename))
    except ValueError:
        abort(404)
    except NoResultFound:
        abort(404)

    resp = current_app.storage.send(f.storage_id, f.filename, f.content_type, current_app.config['FORCE_DOWNLOAD'])
    resp.content_length = f.size

    return resp


@frontend.route('/edit-permissions/', methods = ('GET', 'POST'))
@require_permission('change_user_and_groups')
def edit_permissions():
    form = forms.SelectUser(request.form)
    if form.validate_on_submit():
        return redirect(url_for('edit_permissions_for_user', user_id = form.user.data.id))
    form_markup = render_template('select_user_form.xhtml', form = form)
    return render_template('base.xhtml', unsafe_content = form_markup)


@frontend.route('/edit-permissions/<int:user_id>/', methods = ('GET', 'POST'))
def edit_permissions_for_user(user_id = None):
    user = current_app.session.query(model.User).get(user_id)
    form = forms.create_permissions_form(request.form, groups = (group.id for group in user.groups))
    if form.validate_on_submit():
        # update groups
        user.groups = [group for group in current_app.session.query(model.Group).filter(model.Group.id.in_(form.groups.data)).all()]
        current_app.session.add(user)
        current_app.session.commit()
        return redirect(url_for('edit_permissions'))
    form_markup = render_template('permissions_form.xhtml', form = form, user = user)
    return render_template('base.xhtml', unsafe_content = form_markup)


@frontend.route('/create-token/')
@require_login
@require_permission('create_token')
def create_upload_token():
    token = model.UploadToken(owner = g.user)
    current_app.session.add(token)
    current_app.session.commit()

    return render_template('token_created.xhtml', token = token.id.hex, signature = token.get_signature(), tokenstring = token.id.hex + token.get_signature())


@frontend.route('/api/token-upload', methods = ('POST',))
def api_token_upload():
    # check credentials
    try:
        token = model.UploadToken.get_checked_token(request.headers['X-Dope-Token'], request.headers['X-Dope-Signature'])
    except (ValueError, KeyError, model.UploadToken.InvalidTokenException), e:
        debug('aborting api upload: %r',e)
        abort(403)

    # store file
    w = werkzeug.datastructures.FileStorage(
        stream = request.stream,
        filename = request.headers.get('X-Dope-Filename', None),
        content_type = request.content_type,
        content_length = request.content_length
    )

    f = model.File(current_app.storage, w)
    current_app.session.add(f)
    current_app.session.commit()

    return f.absolute_download_url


@frontend.route('/')
def index():
    return render_template('index.xhtml', title = 'This is DOPE.')
