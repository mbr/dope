#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='dope',
    version='2.0.dev1',
    description='Host files, locally or on S3.',
    long_description=read('README.rst'),
    author='Marc Brinkmann',
    author_email='git@marcbrinkmann.de',
    url='http://github.com/mbr/dope',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    install_requires=['flask', 'flask-appconfig', 'flask-sqlalchemy', 'click',
                      'sqlalchemy-utils', 'blinker', 'passlib'],
    classifiers=[
        'Programming Language :: Python :: 2',
    ],
    entry_points={
        'console_scripts': [
            'dope = dope.cli:cli'
        ]
    }
)
