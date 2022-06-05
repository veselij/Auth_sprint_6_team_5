from enum import Enum


class Msg(Enum):
    created = {"msg": "Object successfully created"}
    unauthorized = {"msg": "Unauthorized"}
    unauthorized_totp = {"msg": "Not synced TOTP"}
    ok = {"msg": "Success"}
    not_found = {"msg": "Object not found"}
    alredy_exists = {"msg": "Object already exists"}
    forbidden = {"msg": "Token invalid"}
    rate_limit = {"msg": "Too Many Requests"}
