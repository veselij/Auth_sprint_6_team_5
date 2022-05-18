import os
from functools import wraps
from http import HTTPStatus

from flask import jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from db.cache import get_cache_access, get_cache_refresh
from models.db_models import get_user_by_id
from services.users import check_refresh_token, check_revoked_token


def jwt_verification(superuser_only=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            jwt_uuid = get_jwt_identity()
            request_uuid = os.path.basename(request.path)
            if not superuser_only and jwt_uuid == request_uuid:
                return fn(*args, **kwargs)

            user = get_user_by_id(jwt_uuid)

            if user and user.is_superuser:
                return fn(*args, **kwargs)
            elif not user:
                return jsonify(msg="User not found"), HTTPStatus.NOT_FOUND.value
            else:
                return jsonify(msg="Access Denied"), HTTPStatus.UNAUTHORIZED.value

        return decorator

    return wrapper


def revoked_token_check():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            token = get_jwt()
            user = get_jwt_identity()
            if check_revoked_token(user, get_cache_access(), token):
                return jsonify({"msg": "Wrong login or password"}), HTTPStatus.UNAUTHORIZED.value
            return fn(*args, **kwargs)

        return decorator

    return wrapper
