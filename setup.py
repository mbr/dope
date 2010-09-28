#!/usr/bin/env python
# coding=utf8

from dope import db
import model
import acl

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

# create base ACL
db.session.commit()
