from enum import Enum

from flasgger import Schema, fields
from marshmallow.validate import OneOf, Range

from social.providers import Providers


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
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)


class RequestIdSchema(Schema):
    request_id = fields.Str(required=True)
    totp_active = fields.Bool()


class SocialTokenSchema(TokenSchema):
    required_fields = fields.List(fields.Str())


class AllDevicesSchema(Schema):
    all_devices = fields.Str(required=True, validate=OneOf(["true", "false"]))


class UserUUIDSchema(Schema):
    user_id = fields.UUID(required=True)


class RoleUUIDSchema(Schema):
    role_id = fields.UUID(required=True)


class UserHistorySchema(Schema):
    id = fields.UUID()
    user_id = fields.UUID()
    user_agent = fields.Str()
    login_date = fields.DateTime()
    login_status = fields.Bool()


class PaginationSchema(Schema):
    page_num = fields.Int(validate=Range(DefaultPaginator.min_page_num.value, DefaultPaginator.max_page_num.value))
    page_items = fields.Int(
        validate=Range(DefaultPaginator.min_page_items.value, DefaultPaginator.max_page_items.value),
    )


class UserHistoryQuerySchema(PaginationSchema):
    year = fields.Int()
    month = fields.Int(validate=Range(1, 12))


class RoleSchema(Schema):
    id = fields.UUID(required=False)
    role = fields.Str(required=True)
    description = fields.Str(required=True)


class UserRoleSchema(Schema):
    role_id = fields.List(fields.UUID(), required=True)


class CheckAccessTokenSchema(Schema):
    access_token = fields.Str(required=True)


class ProvidersSchema(Schema):
    provider = fields.Str(required=True, validate=OneOf([field.name for field in Providers]))


class TotpCodeSchema(Schema):
    code = fields.Str(required=True)


class ProvisioningUrlSchema(Schema):
    url = fields.Str(required=True)
