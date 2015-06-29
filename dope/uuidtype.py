import uuid
import sqlalchemy.types as types

class UUID(types.TypeDecorator):
    # FIXME: in postgres, use UUID type
    #        in other DBs, use blobs or VARCHARs?
    impl = types.String

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return uuid.UUID(value)
