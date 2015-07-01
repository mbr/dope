from uuid import UUID

from werkzeug.routing import BaseConverter


class UUIDConverter(BaseConverter):
    to_python = UUID
    to_url = str
