#!/usr/bin/env python
# coding=utf8

class FileStore(object):
	def __init__(self, dsn, path):
		self.dsn = dsn
		self.path = path

	def store(self, storage):
		# obtain new id
		id = 1

