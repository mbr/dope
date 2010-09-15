#!/usr/bin/env python
# coding=utf8

import os
import uuid
import logging
from datetime import datetime
import hashlib

from Crypto.Util.randpool import RandomPool

import uuidtype

from flask import url_for, send_file
from app import *

randpool = RandomPool()
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

	def send(self, file_id, filename, mimetype):
		filepath = self._filename_from_uuid(file_id)

		return send_file(filepath, mimetype,
		                   as_attachment = True,
		                   attachment_filename = filename)

	def size_of(self, file_id):
		return os.path.getsize(self._filename_from_uuid(file_id))

	def _filename_from_uuid(self, id):
		print(repr(id))
		assert(isinstance(id, uuid.UUID))
		return os.path.join(self.path, str(id))

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)

	def __str__(self):
		return "<User:%d (%s)>" % (self.id, ", ".join(map(str, self.openids)))

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
		key_base = '%s:::%s:::%s:::%s:::%d:::%s:::%s:::%s' % (self.filename, self.storage_id, self.uploaded, self.expires, self.size, self.content_type, repr(randpool.get_bytes(app.config['RANDOM_BYTES_PER_ID'])), app.config['SECRET_KEY'])
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

class ACLAction(db.Model):
	__tablename__ = 'acl_actions'
	id = db.Column(db.Integer, primary_key = True)
	identifier = db.Column(db.String, index = True, unique = True)

	def __init__(self, identifier):
		self.identifier = identifier

	def __str__(self):
		return self.identifier

class ACLPair(db.Model):
	__tablename__ = 'acl'
	__table_args__ = db.UniqueConstraint('value','priority','user_id','action_id')

	# we want to be sqlite compatible, but sqlite cannot handle
	# multi-column primary keys properly. the UniqueConstraint above is actually
	# a workaround for this, without it, we would not need the "id" column
	id = db.Column(db.Integer, primary_key = True)

	user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable = True)
	action_id = db.Column(db.Integer, db.ForeignKey(ACLAction.id))
	value = db.Column(db.Integer)
	priority = db.Column(db.Integer)

	action = db.relation(ACLAction)
	user = db.relation(User)

	def __init__(self, user, action, value, priority = None):
		self.action = action
		self.user = user
		self.value = value
		if None == priority:
			# get first available priority
			db.session.flush()
			q = db.select([db.func.max(ACLPair.priority)], whereclause = db.and_(ACLPair.user == user, ACLPair.action == action))
			priority = db.session.execute(q).fetchone()[0]
			if None == priority: priority = 0
			else: priority += 1

			self.priority = priority
		else: self.priority = priority
db.Index('unique_acl', ACLPair.user_id, ACLPair.action_id, ACLPair.priority, ACLPair.value)

def check_acl(user, action):
	if not isinstance(action, ACLAction):
		# retrieve action by string
		action = ACLAction.query.filter_by(identifier = str(action)).one()

	# we cannot do everything in a single query, as there is no suppport for nullsfirst in SQLAlchemy yet

	# so, first check for specific ACLs
	if None != user:
		acl = ACLPair.query.filter_by(user = user, action = action).order_by(db.desc(ACLPair.value)).first()
		if acl: return acl.value

	# if no match, look for a generic match next
	acl = ACLPair.query.filter_by(user = None, action = action).order_by(db.desc(ACLPair.value)).first()
	if acl: return acl.value

	raise Exception('ACL ran out of ideas finding %s for %s' % (action, user))
