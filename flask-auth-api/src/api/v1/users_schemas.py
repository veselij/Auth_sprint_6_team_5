from flasgger import Schema, fields


class AuthSchema(Schema):
    login = fields.Str()
    password = fields.Str()


class MsgSchema(Schema):
    msg = fields.Str()


class TokenSchema(Schema):
    access_token = fields.Str()
    refresh_token = fields.Str()
