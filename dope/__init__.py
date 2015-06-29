#!/usr/bin/env python
# coding=utf8

from flask import Flask
from flask_appconfig import AppConfig

import model


def create_app(configfile=None):
    app = Flask(__name__)

    AppConfig(app)

    # init db connection
    app.storage = model.FileStorage(app.config['FILE_STORAGE'])

    # load modules
    #app.register_module(frontend)

    return app
