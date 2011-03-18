#!/usr/bin/env python
# coding=utf8

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

import defaults

CONFIGFILE = 'dope.cfg'

app = Flask('dope')
app.config.from_object(defaults)
app.config.from_pyfile(CONFIGFILE)
db = SQLAlchemy(app)
