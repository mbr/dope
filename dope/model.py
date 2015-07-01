import uuid

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.models import Timestamp


db = SQLAlchemy()


class File(db.Model, Timestamp):
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    hash = db.Column(db.Binary, index=True, nullable=False)
    size = db.Column(db.BigInteger)
    filename = db.Column(db.Unicode)

    @classmethod
    def get_refcount(cls, hash):
        return db.session.query(cls.hash).filter_by(hash=hash).count()

    def get_download_url(self):
        return current_app.storage.get_download_url(self)
