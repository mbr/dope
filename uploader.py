#!/usr/bin/env python
# coding=utf8

import mimetypes
import os

from warnings import warn
from httplib import HTTPConnection
from urlparse import urlparse

try:
	import magic # note: uses supposedly outdated version of python-magic
	# see http://stackoverflow.com/questions/43580/how-to-find-the-mime-type-of-a-file-in-python
	m = magic.open(magic.MAGIC_MIME)
	m.load()
except ImportError:
	warn('python-magic not available, no content-based mimetype guessing available')
	m = None

def guess_mimetype(path):
	mimetype = None
	return m.file(path) or mimetypes.guess_type(path)[0] or None

class Uploader(object):
	def __init__(self, url, token, signature):
		self.token = token
		self.signature = signature
		self.url = urlparse(url)
		if self.url.scheme not in ('http', 'https'): Exception('Unsuppored uploader protocol %r' % protocol)

	def upload_file(self, path, mimetype = None):
		return self.upload(file(path),
		                   os.path.basename(path),
		                   mimetype or guess_mimetype(path) or 'application/octet-stream')

	def upload(self, ufile, filename = 'unnamed_file', mimetype = 'application/octet-stream'):
		if 'https' == self.url.scheme:
			warn('Secure connection request, but verification of the certificate is not implemented')
			self.connection = HTTPSConnection(self.url.netloc)
		else: self.connection = HTTPConnection(self.url.netloc)

		self.connection.set_debuglevel(99999)

		# connect, make first request
		self.connection.connect()

		headers = {
			'X-Dope-Protocol': 1,
			'X-Dope-Token': self.token,
			'X-Dope-Signature': self.signature,
			'User-agent': 'Dope uploader.py',
			'Content-Type': mimetype
		}
		if filename: headers['X-Dope-Filename'] = filename

		self.connection.request('POST', self.url.path, ufile, headers)
		return self.connection.getresponse()


if '__main__' == __name__:
	import sys

	token = '0c63407e39de11e098ea4061868c143d'
	signature = 'a365dc0ae22e38d5169225df9e467e5eac19e72c80ff7ff2f06b3a1f75185ab6'

	uploader = Uploader('http://localhost:5000/api/token-upload', token, signature)
	print uploader.upload_file(sys.argv[1]).read()
