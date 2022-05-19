from enum import Enum


class Msg(Enum):
    created = {"msg": "User successfully created"}
    user_alredy_exists = {"msg": "User alreadt exists"}
    unauthorized = {"msg": "Unauthorized"}
    ok = {"msg": "Success"}
    login_already_exists = {"msg": "Login already exists"}
    not_found = {"msg": "Object not found"}
