#!/usr/bin/env python
# coding=utf8

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

class DopeProtocol(LineReceiver):
	def connectionMade(self):
		self.sendLine("DOPE")
		self.user = None
		self.filesize = None
		self.bytes_received = 0

	def rawDataReceived(self, data):
		print "sinking data %r" % data
		self.bytes_received += len(data)
		if self.bytes_received == self.filesize:
			url = 'http://nowhere.invalid'
			self.sendLine("OK %s" % url)
			self.transport.loseConnection()
		elif self.bytes_received > self.filesize:
			self.sendLine("ERR Too many bytes received")
			self.transport.loseConnection()

	def lineReceived(self, line):
		# first line should be "token signature filesize"
		# check credentials
		token, signature, filesize = line.split(' ')
		self.filesize = int(filesize)

		if False:
			self.sendLine("ERR Bad credentials")
			self.transport.loseConnection()
		elif 0 >= filesize:
			self.sendLine("ERR Bad filesize")
			self.transport.loseConnection()
		else:
			self.sendLine("OK Waiting for %d bytes" % self.filesize)
			self.setRawMode()

class DopeFactory(protocol.ServerFactory):
	protocol = DopeProtocol

reactor.listenTCP(31418, DopeFactory())
reactor.run()
