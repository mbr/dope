#!/usr/bin/env python
# coding=utf8

import os
import uuid
import logging
from datetime import datetime
import hashlib
import Crypto.Random

import uuidtype

import acl

from flask import url_for, send_file
from app import *

class ForkSafeRandom(object):
	def __init__(self):
		self.rng = Crypto.Random.new()

	def read(self, *args, **kwargs):
		try:
			return self.rng.read(*args, **kwargs)
		except AssertionError:
			Crypto.Random.atfork()
			return self.rng.read(*args, **kwargs)

rand = ForkSafeRandom()
debug = app.logger.debug

hashfunc = getattr(hashlib, app.config['HASHFUNC'])
hashsize = hashfunc().digest_size

class FileStorage(object):
	def __init__(self, path):
		self.path = path

	def store(self, file_):
		file_id = uuid.uuid1()

		filename = self._filename_from_uuid(file_id)
		debug("storing at %s", filename)

		file_.save(filename)

		return file_id

	def remove(self, file_id):
		filename = self._filename_from_uuid(file_id)
		debug("removing %s", filename)

		os.unlink(filename)

	def send(self, file_id, filename, mimetype, force_download = True):
		filepath = self._filename_from_uuid(file_id)

		return send_file(filepath, mimetype,
		                   as_attachment = force_download,
		                   attachment_filename = filename)

	def size_of(self, file_id):
		return os.path.getsize(self._filename_from_uuid(file_id))

	def _filename_from_uuid(self, id):
		print(repr(id))
		assert(isinstance(id, uuid.UUID))
		return os.path.join(self.path, str(id))

user_group_table = db.Table('user_group', db.metadata,
                              db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                              db.Column('group_id', db.Integer, db.ForeignKey('groups.id'))
                           )

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	groups = db.relation('Group', secondary = user_group_table, backref = 'users')

	def __str__(self):
		return "<User:%d (%s)>" % (self.id, ", ".join(map(str, self.openids)))

class Group(db.Model, acl.ACLSubjectRef):
	# strictly additive
	__tablename__ = 'groups'
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String, nullable = True, unique = True)

	def __repr__(self):
		return "<Group(id=%r,name=%r)>" % (self.id, self.name)

def get_groups_of(user):
	if None == user: groups = [db.session.query(Group).filter_by(name = 'anonymous').one()]
	else: groups = [db.session.query(Group).filter_by(name = 'registered').one()] + user.groups

	debug('retrieved groups for user %s: %s', user, groups)
	return groups

def user_has_permission(user, verb, obj = None):
	# use strictly additive model
	groups = get_groups_of(user)
	for group in groups:
		perm = group.may(verb, obj)
		debug('checking group %s: %s', group, perm)
		if perm: return True
	return False

class OpenID(db.Model):
	__tablename__ = 'openids'
	id = db.Column(db.String, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey(User.id))
	user = db.relation(User, backref = db.backref('openids'))

	def __init__(self, url, user):
		self.id = url
		self.user = user

	def __str__(self):
		return str(self.id)

def create_new_user(openid_url):
	u = User()
	o = OpenID(openid_url, u)
	db.session.add(u)
	db.session.add(o)
	db.session.commit()

	debug('created new user: %s', u)
	return u

class UploadToken(db.Model):
	class InvalidTokenException(Exception): pass
	__tablename__ = 'tokens'
	id = db.Column(uuidtype.UUID, primary_key = True)
	owner_id = db.Column(db.Integer, db.ForeignKey(User.id))
	owner = db.relation(User, backref = db.backref('owned_tokens'))

	def __init__(self, id = None, **kwargs):
		kwargs['id'] = id or uuid.uuid1()
		super(UploadToken, self).__init__(**kwargs)

	def get_signature(self, key = None):
		clearinp = '%s||KEY||%s' % (self.id.hex, key or app.config['SECRET_KEY'])
		return hashfunc(clearinp).hexdigest()

	def check_signature(self, signature, key = None):
		return signature == self.get_signature(key)

	@classmethod
	def get_checked_token(class_, token_as_string, signature):
		token_id = uuid.UUID(token_as_string)
		token = db.session.query(class_).get(token_id)
		if not token.check_signature(signature): raise class_.InvalidTokenException('Signature does not match')
		return token


class File(db.Model):
	__tablename__ = 'files'

	id = db.Column(db.Integer, primary_key = True)
	filename = db.Column(db.Unicode)
	storage_id = db.Column(uuidtype.UUID)
	public_id = db.Column(uuidtype.UUID)
	uploaded = db.Column(db.DateTime)
	expires = db.Column(db.DateTime)
	size = db.Column(db.Integer)
	times_downloaded = db.Column(db.Integer)
	content_type = db.Column(db.String)
	access_key = db.Column(db.String)
	owner_id = db.Column(db.Integer, db.ForeignKey(User.id))
	owner = db.relation(User, backref = db.backref('owned_files'))

	def __init__(self, storage, file_, ttl_delta = None):
		# id: primary key
		self.filename = file_.filename
		self.storage_id = storage.store(file_)
		self.uploaded = datetime.now()
		self.expires = ttl_delta if ttl_delta else None
		self.size = storage.size_of(self.storage_id)
		self.times_downloaded = 0
		self.content_type = file_.content_type

		# generate keys for access
		key_base = '%s:::%s:::%s:::%s:::%d:::%s:::%s:::%s' % (self.filename, self.storage_id, self.uploaded, self.expires, self.size, self.content_type, repr(rand.read(app.config['RANDOM_BYTES_PER_ID'])), app.config['SECRET_KEY'])
		self.access_key = hashfunc(key_base).hexdigest()
		self.public_id = uuid.uuid4()

		debug("RANDOM KEY %s", key_base)
		debug("SECRET HASH %s", self.access_key)
		debug("PUBLIC ID %s", self.public_id)

		debug("SIZE (content-length) %d", self.size)

	def __str__(self):
		return 'File #%d "%s", storage id %s' % (self.id, self.filename, self.storage_id)

	@property
	def download_url(self):
		return url_for('download', public_id = str(self.public_id))

	@property
	def absolute_download_url(self):
		return url_for('download', public_id = str(self.public_id), _external = True)
