#!/usr/bin/env python
# coding=utf8

import hashlib

import Crypto.Random
from flask import current_app

class ForkSafeRandom(object):
	def __init__(self):
		self.rng = Crypto.Random.new()

	def read(self, *args, **kwargs):
		try:
			return self.rng.read(*args, **kwargs)
		except AssertionError:
			Crypto.Random.atfork()
			return self.rng.read(*args, **kwargs)


def hashfunc(*args, **kwargs):
	hf = getattr(hashlib, current_app.config['HASHFUNC'])
	return hf(*args, **kwargs)
