from flask import Flask
from flask_appconfig import AppConfig
from flask_bootstrap import Bootstrap

from .frontend import frontend
from .model import db


def create_app(configfile=None):
    app = Flask(__name__)

    AppConfig(app)
    Bootstrap(app)
    db.init_app(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    app.register_blueprint(frontend)

    return app
