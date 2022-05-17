import os
from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from models.db_models import User


def jwt_verification(superuser_only=False):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            jwt_uuid = get_jwt_identity()
            request_uuid = os.path.basename(request.path)
            if not superuser_only and jwt_uuid == request_uuid:
                return fn(*args, **kwargs)
            elif User.query.filter_by(login=jwt_uuid).first().is_superuser:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Access Denied"), 403

        return decorator

    return wrapper
