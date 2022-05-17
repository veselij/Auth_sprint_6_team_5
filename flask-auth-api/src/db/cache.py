from typing import Optional, Protocol, Type

from redis import ConnectionPool, Redis
from redis.exceptions import ConnectionError

from core.config import config

POOL_ACCESS_TOKENS = ConnectionPool(host=config.redis_host, port=config.redis_port, db=0)
POOL_REFRESH_TOKENS = ConnectionPool(host=config.redis_host, port=config.redis_port, db=1)


class Cache(Protocol):
    def get(self, name: str) -> Optional[bytes]:
        ...

    def set(self, name: str, value: str, ex: int) -> Optional[bool]:
        ...


def get_cache_access() -> tuple[Redis, Type[Exception]]:
    return Redis(connection_pool=POOL_ACCESS_TOKENS), ConnectionError


def get_cache_refresh() -> tuple[Redis, Type[Exception]]:
    return Redis(connection_pool=POOL_REFRESH_TOKENS), ConnectionError
