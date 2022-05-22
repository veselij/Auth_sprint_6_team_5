from enum import Enum


class Msg(Enum):
    created = {"msg": "Object successfully created"}
    unauthorized = {"msg": "Unauthorized"}
    ok = {"msg": "Success"}
    not_found = {"msg": "Object not found"}
    alredy_exists = {"msg": "Object already exists"}
