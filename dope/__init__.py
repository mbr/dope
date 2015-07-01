from flask import Flask
from flask_appconfig import AppConfig
from flask_bootstrap import Bootstrap

from . import storage
from .frontend import frontend
from .model import db


def create_app(configfile=None):
    app = Flask(__name__)

    AppConfig(app)
    Bootstrap(app)
    db.init_app(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    if app.config['STORAGE_TYPE'] == 'filesystem':
        app.storage = storage.FilesystemStorage(
            app.config['STORAGE_FS_PATH'],
            app.config['STORAGE_FS_URL_PREFIX'],
        )
    else:
        raise ValueError(
            'Invalid storage type: {}'.format(app.config['STORAGE_TYPE']))

    app.register_blueprint(frontend)

    return app
