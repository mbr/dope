#!/usr/bin/env python
# coding=utf8

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

CONFIGFILE = 'dope.cfg'

app = Flask('dope')
app.config.from_pyfile(CONFIGFILE)
db = SQLAlchemy(app)
