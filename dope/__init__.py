from flask import Flask
from flask_appconfig import AppConfig

from .frontend import frontend
from .model import db


def create_app(configfile=None):
    app = Flask(__name__)

    AppConfig(app)
    db.init_app(app)

    app.register_blueprint(frontend)

    return app
