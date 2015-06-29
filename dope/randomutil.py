#!/usr/bin/env python
# coding=utf8

import hashlib

from flask import current_app

def hashfunc(*args, **kwargs):
    hf = getattr(hashlib, current_app.config['HASHFUNC'])
    return hf(*args, **kwargs)
