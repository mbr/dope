#!/usr/bin/env python
# coding=utf8

import sys

from dope import db
import model
import acl

def read_yesno():
	while True:
		l = sys.stdin.readline()
		if l.lower().startswith('y'): return True
		if l.lower().startswith('n'): return False
		sys.stdout.write('Please enter "yes" or "no": ')


def read_openid():
	while True:
		sys.stdout.write('Enter the OpenID for the admin account: ')
		openid = sys.stdin.readline().strip()
		sys.stdout.write('Using OpenID "%s". Is that correct? ' % openid)
		if read_yesno(): return openid

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

# the following acl verbs are recognized:
# register
# upload_file
# download_file
# delete_file
# create_tickets

anonymous.permit('register')
anonymous.permit('download_file')

uploaders.permit('upload_file')

admins.permit('upload_file')
admins.permit('download_file')
admins.permit('delete_file')
admins.permit('create_tickets')

# create admin account
u = model.create_new_user(openid)
u.groups.append(admins)
db.session.commit()
