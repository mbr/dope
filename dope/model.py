import uuid

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types import uuid as UUID
from sqlalchemy_utils.models import Timestamp


db = SQLAlchemy()


class File(db.Model, Timestamp):
    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    hash = db.Column(db.String, index=True, nullable=False)
    size = db.Column(db.BigInteger)
    filename = db.Column(db.Unicode)
