from flask import Flask
from flask_appconfig import AppConfig
from flask_bootstrap import Bootstrap

from . import storage
from .frontend import frontend
from .model import db
from .util import UUIDConverter


def create_app(configfile=None):
    app = Flask(__name__)

    app.url_map.converters['uuid'] = UUIDConverter

    AppConfig(app)
    Bootstrap(app)
    db.init_app(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    if app.config['STORAGE_TYPE'] == 'filesystem':
        app.storage = storage.FilesystemStorage(
            app.config['STORAGE_FS_PATH'],
            app.config['STORAGE_FS_URL_PREFIX'],
        )
    elif app.config['STORAGE_TYPE'] == 's3':
        import boto

        con = boto.connect_s3(
            app.config['BOTO_ACCESS_KEY'],
            app.config['BOTO_SECRET_KEY'],
        )

        bucket = con.get_bucket(app.config['BOTO_BUCKET_NAME'])

        app.storage = storage.BotoStorage(
            bucket,
            app.config['BOTO_REDUCED_REDUNDANCY']
        )
    else:
        raise ValueError(
            'Invalid storage type: {}'.format(app.config['STORAGE_TYPE']))

    app.register_blueprint(frontend)

    return app
