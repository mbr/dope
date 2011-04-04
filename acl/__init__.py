#!/usr/bin/env python
# coding=utf8

from sqlalchemy import create_engine, Column, Integer, String, Sequence, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.util import classproperty
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.session import object_session

Base = declarative_base()

class ACLSubject(Base):
	__tablename__ = 'acl_subjects'
	id = Column(Integer, primary_key = True)

	def may(self, verb, obj = None):
		session = object_session(self)
		verb = ACLVerb.get(session, verb)
		obj = ACLObject.get_object(obj)

		value = None

		for rule in session.query(ACLRule).filter_by(subj = self, verb = verb, obj = obj).all():
			if False == rule.value: return False
			elif True == rule.value: value = True
			else:
				assert('not reached')

		return value

	def permit(self, verb, obj = None, value = True):
		session = object_session(self)
		verb = ACLVerb.get(session, verb)
		obj = ACLObject.get_object(obj)

		# check if rule exists, if yes, return
		if session.query(ACLRule).filter_by(subj = self, verb = verb, obj = obj, value = value).first(): return

		# create rule
		r = ACLRule(subj = self, verb = verb, obj = obj, value = value)
		session.add(r)

class ACLVerb(Base):
	__tablename__ = 'acl_verbs'
	id = Column(Integer, primary_key = True)
	name = Column(String, unique = True)

	def __init__(self, name):
		self.name = name

	@staticmethod
	def get_by_name(session, name):
		session.flush()
		verb = session.query(ACLVerb).filter_by(name = name).first()

		if not verb:
			verb = ACLVerb(name)
			session.add(verb)
			session.flush()
		return verb

	@staticmethod
	def get(session, name_or_verb):
		if isinstance(name_or_verb, ACLVerb): return name_or_verb
		return ACLVerb.get_by_name(session, name_or_verb)

class ACLObject(Base):
	__tablename__ = 'acl_objects'
	id = Column(Integer, primary_key = True)

	@staticmethod
	def get_object(acl_obj):
		if None == acl_obj: return None
		if isinstance(acl_obj, ACLObjectRef):
			acl_obj.init_acl()
			return acl_obj._acl_object
		return acl_obj

class ACLSubjectRef(object):
	@classproperty
	def _acl_subject_id(cls):
		return Column(Integer, ForeignKey(ACLSubject.id))

	@classproperty
	def _acl_subject(cls):
		return relationship(ACLSubject)

	def init_acl(self):
		if None == self._acl_subject:
			self._acl_subject = ACLSubject()

	def may(self, *args, **kwargs):
		self.init_acl()
		return self._acl_subject.may(*args, **kwargs)

	def permit(self, *args, **kwargs):
		self.init_acl()
		return self._acl_subject.permit(*args, **kwargs)

class ACLObjectRef(object):
	@classproperty
	def _acl_object_id(cls):
		return Column(Integer, ForeignKey(ACLObject.id))

	@classproperty
	def _acl_object(cls):
		return relationship(ACLObject)

	def init_acl(self):
		if None == self._acl_object:
			self._acl_object = ACLObject()

class ACLRule(Base):
	__tablename__ = 'acl_rules'
	id = Column(Integer, primary_key = True)

	subj_id = Column(Integer, ForeignKey(ACLSubject.id))
	verb_id = Column(Integer, ForeignKey(ACLVerb.id))
	obj_id = Column(Integer, ForeignKey(ACLObject.id), nullable = True)

	subj = relationship(ACLSubject)
	verb = relationship(ACLVerb)
	obj = relationship(ACLObject)

	value = Column(Boolean)
