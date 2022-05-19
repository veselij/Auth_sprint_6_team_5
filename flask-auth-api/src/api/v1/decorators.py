import os
from functools import wraps
from http import HTTPStatus

from flask import jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from api.v1.msg import Msg
from api.v1.users_schemas import MsgSchema
from services.users import check_revoked_token, get_user


def jwt_verification(superuser_only=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            jwt_uuid = get_jwt_identity()
            request_uuid = os.path.basename(request.path)
            if not superuser_only and jwt_uuid == request_uuid:
                return fn(*args, **kwargs)
            user = get_user(jwt_uuid)
            if user and user.is_superuser:
                return fn(*args, **kwargs)
            elif not user:
                return jsonify(MsgSchema().dump(Msg.not_found.value)), HTTPStatus.NOT_FOUND.value
            else:
                return jsonify(MsgSchema().dump(Msg.unauthorized.value)), HTTPStatus.UNAUTHORIZED.value

        return decorator

    return wrapper


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
