from dataclasses import dataclass
from typing import Optional, Protocol, Type

from redis import ConnectionPool, Redis
from redis.exceptions import ConnectionError

from core.config import config, logger
from utils.decorators import backoff
from utils.exceptions import RetryExceptionError

POOL_ACCESS_TOKENS = ConnectionPool(host=config.redis_host, port=config.redis_port, db=0)
POOL_REFRESH_TOKENS = ConnectionPool(host=config.redis_host, port=config.redis_port, db=1)


class Cache(Protocol):
    def get(self, name: str) -> Optional[bytes]:
        ...

    def set(self, name: str, value: str, ex: int) -> Optional[bool]:
        ...

    def delete(self, *names: str) -> Optional[int]:
        ...


@dataclass
class CacheManager:
    cache: Cache
    exc: Type[Exception]

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def get_value(self, key: str) -> Optional[str]:
        try:
            value = self.cache.get(key)
        except self.exc:
            raise RetryExceptionError("Cache is not available")
        if value:
            return value.decode()
        return

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def set_value(self, name: str, value: str, ex: int) -> None:
        try:
            self.cache.set(name, value, ex)
        except self.exc:
            raise RetryExceptionError("Cache is not available")

    @backoff(logger, start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def delete_value(self, name: str) -> Optional[bool]:
        try:
            self.cache.delete(name)
        except self.exc:
            raise RetryExceptionError("Cache is not available")


def get_cache_access() -> CacheManager:
    return CacheManager(Redis(connection_pool=POOL_ACCESS_TOKENS), ConnectionError)


def get_cache_refresh() -> CacheManager:
    return CacheManager(Redis(connection_pool=POOL_REFRESH_TOKENS), ConnectionError)
