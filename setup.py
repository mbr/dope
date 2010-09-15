#!/usr/bin/env python
# coding=utf8

from dope import db
from model import ACLPair, ACLAction

db.drop_all()
db.create_all()

# create actions
upload_files = ACLAction('upload_files')
db.session.add(upload_files)

# create base ACL
db.session.add(ACLPair(None, upload_files, False))
db.session.commit()
