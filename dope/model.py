#!/usr/bin/env python
# coding=utf8

import os
import uuid
import logging
from datetime import datetime

import acl
from flask import url_for, send_file, g
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, Table, Integer, String, ForeignKey, Unicode, DateTime

import uuidtype
from randomutil import ForkSafeRandom

rand = ForkSafeRandom()
debug = logging.debug

Base = declarative_base()

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
		assert(isinstance(id, uuid.UUID))
		return os.path.join(self.path, str(id))

user_group_table = Table('user_group', Base.metadata,
                              Column('user_id', Integer, ForeignKey('users.id')),
                              Column('group_id', Integer, ForeignKey('groups.id'))
                           )


class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key = True)
	groups = relationship('Group', secondary = user_group_table, backref = 'users')

	def __str__(self):
		return "<User:%d (%s)>" % (self.id, ", ".join(map(str, self.openids)))


class Group(Base, acl.ACLSubjectRef):
	# strictly additive
	__tablename__ = 'groups'
	id = Column(Integer, primary_key = True)
	name = Column(String, nullable = True, unique = True)

	def __repr__(self):
		return "<Group(id=%r,name=%r)>" % (self.id, self.name)


def get_groups_of(user):
	if None == user: groups = [g.session.query(Group).filter_by(name = 'anonymous').one()]
	else: groups = [g.session.query(Group).filter_by(name = 'registered').one()] + user.groups

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


class OpenID(Base):
	__tablename__ = 'openids'
	id = Column(String, primary_key = True)
	user_id = Column(Integer, ForeignKey(User.id))
	user = relationship(User, backref = backref('openids'))

	def __init__(self, url, user):
		self.id = url
		self.user = user

	def __str__(self):
		return str(self.id)


def create_new_user(openid_url):
	u = User()
	o = OpenID(openid_url, u)
	g.session.add(u)
	g.session.add(o)
	g.session.commit()

	debug('created new user: %s', u)
	return u


class UploadToken(Base):
	class InvalidTokenException(Exception): pass
	__tablename__ = 'tokens'
	id = Column(uuidtype.UUID, primary_key = True)
	owner_id = Column(Integer, ForeignKey(User.id))
	owner = relationship(User, backref = backref('owned_tokens'))

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
		token = g.session.query(class_).get(token_id)
		if not token.check_signature(signature): raise class_.InvalidTokenException('Signature does not match')
		return token


class File(Base):
	__tablename__ = 'files'

	id = Column(Integer, primary_key = True)
	filename = Column(Unicode)
	storage_id = Column(uuidtype.UUID)
	public_id = Column(uuidtype.UUID)
	uploaded = Column(DateTime)
	expires = Column(DateTime)
	size = Column(Integer)
	times_downloaded = Column(Integer)
	content_type = Column(String)
	access_key = Column(String)
	owner_id = Column(Integer, ForeignKey(User.id))
	owner = relationship(User, backref = backref('owned_files'))

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
