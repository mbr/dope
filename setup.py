#!/usr/bin/env python
# coding=utf8

from distutils.core import setup

setup(name = 'Dope',
      version = '0.1',
      description = 'File uploading made easy (WSGI app).',
      author = 'Marc Brinkmann',
      url = 'https://github.com/mbr/dope',
      packages = ['dope', 'acl'],
      # requirements for acl are just sqlalchemy
      install_requires = ['sqlalchemy>=0.6.6', 'flask', 'Flask-SQLAlchemy', 'Flask-WTF', 'pycrypto>=2.3'],
      scripts = ['init_dope_db', 'quicksend'],
      package_data = {'dope': ['static/js/*', 'static/css/*', 'static/img/*.*', 'static/img/plupload/*', 'static/img/social_icons/*', 'templates/*']},
      zip_safe = False,
     )
