from typing import NamedTuple, Union

from flask_jwt_extended import create_access_token, create_refresh_token, get_jti


class Token(NamedTuple):
    access_token: str
    refresh_token: str
    required_fields: list


def get_token(user_id: str, is_superuser: Union[bool, int], roles: list, required_fields: list) -> Token:
    access_token = create_access_token(
        identity=user_id,
        additional_claims={"roles": roles, "admin": int(is_superuser)},
    )
    refresh_token = create_refresh_token(
        identity=user_id,
        additional_claims={"related_access_token": get_jti(access_token), "admin": int(is_superuser)},
    )
    return Token(access_token, refresh_token, required_fields)
