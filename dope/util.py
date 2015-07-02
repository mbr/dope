from uuid import UUID

from werkzeug.routing import BaseConverter


class UUIDConverter(BaseConverter):
    to_python = UUID

    def to_url(self, obj):
        return str(obj).replace('-', '')
