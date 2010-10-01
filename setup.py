#!/usr/bin/env python
# coding=utf8

import sys
import os

from dope import db
import model
import acl

def read_yesno(msg = None):
	while True:
		if msg: sys.stdout.write(msg)
		sys.stdout.write(' ')
		l = sys.stdin.readline()
		if l.lower().startswith('y'): return True
		if l.lower().startswith('n'): return False
		sys.stdout.write('\nPlease enter "yes" or "no".\n')

def read_openid():
	while True:
		sys.stdout.write('Enter the OpenID for the admin account: ')
		openid = sys.stdin.readline().strip()
		if not openid.startswith('http'):
			sys.stdout.write('That is not a valid OpenID (does not start with "http")' + os.linesep)
			continue
		if read_yesno('Using OpenID "%s". Is that correct?' % openid): return openid

openid = read_openid()

db.drop_all()
db.create_all()
acl.Base.metadata.bind = db.engine
acl.Base.metadata.drop_all()
acl.Base.metadata.create_all()

# create initial groups
anonymous = model.Group(name = 'anonymous') # pseudo-group
registered = model.Group(name = 'registered') # pseudo-group

uploaders = model.Group(name = 'uploaders')
admins = model.Group(name = 'admins')

db.session.add_all([anonymous, registered, uploaders, admins])

# acl setup: base groups, user is in one or the other
anonymous.permit('register')
anonymous.permit('download_file')
registered.permit('download_file')

# extra groups
uploaders.permit('upload_file')

admins.permit('upload_file')
admins.permit('download_file')
admins.permit('delete_file')
admins.permit('create_tickets')
admins.permit('change_user_and_groups')

# create admin account
u = model.create_new_user(openid)
u.groups.append(admins)
db.session.commit()
