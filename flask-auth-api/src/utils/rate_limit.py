import datetime
from functools import wraps
from http import HTTPStatus

from flask import request
from flask.helpers import make_response
from flask.json import jsonify
from redis import ConnectionError, ConnectionPool, Redis

from core.config import config, logger
from core.msg import Msg
from models.users_response_schemas import MsgSchema
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError

REDIS_CONN = Redis(connection_pool=ConnectionPool(host=config.redis_host, port=config.redis_port, db=5))


def rate_limiting(requests_limit: int = 20, limit_expire_period: int = 60):
    """Limit requests per received limit period.

    Args:
        requests_limit: int requests limit
        limit_expire_period: int limit period
    """

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if requests_is_limited(request_limit=requests_limit, limit_key_expire_period=limit_expire_period):
                return make_response(
                    jsonify(MsgSchema().load(Msg.rate_limit.value)), HTTPStatus.TOO_MANY_REQUESTS.value
                )
            return func(*args, **kwargs)

        return inner

    return wrapper


@backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
def requests_is_limited(request_limit, limit_key_expire_period):
    request_ip = request.headers.get("X-Real-IP")
    now = datetime.datetime.now()
    key = f"{request_ip}:{now.minute}"
    try:
        pipe = REDIS_CONN.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, limit_key_expire_period)
        result = pipe.execute()
    except ConnectionError:
        raise RetryExceptionError("Redis not available")
    return result[0] > request_limit
