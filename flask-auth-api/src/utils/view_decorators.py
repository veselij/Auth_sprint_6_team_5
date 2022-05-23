import json
import os
from functools import wraps
from http import HTTPStatus

from flask import jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from core.config import config
from core.msg import Msg
from db.cache import Caches
from models.users_response_schemas import MsgSchema

caches = Caches()


def jwt_verification(superuser_only=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            token = get_jwt()
            jwt_uuid = token["sub"]
            request_uuid = os.path.basename(request.path)
            if not superuser_only and jwt_uuid == request_uuid:
                return fn(*args, **kwargs)
            admin = token.get("admin", None)
            if admin == 1:
                return fn(*args, **kwargs)
            else:
                return jsonify(MsgSchema().dump(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value

        return decorator

    return wrapper


def check_revoked_token(user_id: str, token: dict) -> bool:
    if "related_access_token" in token:
        access_token = token["related_access_token"]
        exp = token["exp"] - config.refresh_ttl
    else:
        access_token = token["jti"]
        exp = token["exp"] - config.access_ttl
    revoked_tokens = caches.access_cache.get_value(user_id)
    if not revoked_tokens:
        return False
    revoked_tokens = json.loads(revoked_tokens)
    if "all" in revoked_tokens:
        return exp <= float(revoked_tokens["all"])
    token_revoke_time = revoked_tokens.get(access_token, None)
    if token_revoke_time is None:
        return False
    return exp <= float(token_revoke_time)


def revoked_token_check():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            token = get_jwt()
            user = get_jwt_identity()
            if check_revoked_token(user, token):
                return jsonify(MsgSchema().dump(Msg.not_found.value)), HTTPStatus.UNAUTHORIZED.value
            return fn(*args, **kwargs)

        return decorator

    return wrapper
