import datetime
from functools import wraps
from http import HTTPStatus
from redis import ConnectionPool, Redis
from core.config import config


from flask import request
from flask.helpers import make_response
from flask.json import jsonify

from core.msg import Msg
from models.users_response_schemas import MsgSchema

REDIS_CONN = Redis(connection_pool=ConnectionPool(host=config.redis_host, port=config.redis_port, db=5))
REQUEST_LIMIT = 10
LIMIT_KEY_EXPIRE_PERIOD = 60


def rate_limiting(requests_limit: int = 10, limit_expire_period: int = 60):
    """Limit requests per received limit period.

        Args:
            requests_limit: int requests limit
            limit_expire_period: int limit period
        """
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if requests_is_limited(request_limit=requests_limit, limit_key_expire_period=limit_expire_period):
                make_response(jsonify(MsgSchema().load(Msg.rate_limit.value)), HTTPStatus.TOO_MANY_REQUESTS.value)
            func(*args, **kwargs)
            return
        return inner
    return wrapper


def requests_is_limited(request_limit, limit_key_expire_period):
    request_ip = request.headers.get('X-Real-IP')
    now = datetime.datetime.now()
    pipe = REDIS_CONN.pipeline()
    key = f'{request_ip}:{now.minute}'
    pipe.incr(key, 1)
    pipe.expire(key, limit_key_expire_period)
    result = pipe.execute()
    return result[0] > request_limit
