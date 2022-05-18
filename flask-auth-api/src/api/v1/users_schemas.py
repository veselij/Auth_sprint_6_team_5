from enum import Enum

from flasgger import Schema, fields
from marshmallow.validate import OneOf, Range


class DefaultPaginator(Enum):
    page_num = 1
    page_items = 20
    min_page_num = 1
    min_page_items = 1
    max_page_num = 100
    max_page_items = 100


class AuthSchema(Schema):
    login = fields.Str(required=True)
    password = fields.Str(required=True)


class MsgSchema(Schema):
    msg = fields.Str(required=True)


class TokenSchema(Schema):
    access_token = fields.UUID(required=True)
    refresh_token = fields.UUID(required=True)


class AllDevicesSchema(Schema):
    all_devices = fields.Str(required=True, validate=OneOf(["true", "false"]))


class UserUUIDSchema(Schema):
    user_id = fields.UUID(required=True)


class UserHistorySchema(Schema):
    id = fields.UUID()
    user_id = fields.UUID()
    user_agent = fields.Str()
    login_date = fields.DateTime()
    login_status = fields.Bool()


class PaginationSchema(Schema):
    page_num = fields.Int(validate=Range(DefaultPaginator.min_page_num.value, DefaultPaginator.max_page_num.value))
    page_items = fields.Int(
        validate=Range(DefaultPaginator.min_page_items.value, DefaultPaginator.max_page_items.value)
    )
