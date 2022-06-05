import aioredis
import pytest_asyncio
from settings import config


@pytest_asyncio.fixture(scope="session")
async def redis_client():
    client = await aioredis.from_url(
        "redis://{0}:{1}".format(config.redis_host, config.redis_port), db=4, decode_responses=True
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def clear_redis(redis_client):
    await redis_client.flushall(asynchronous=False)


@pytest_asyncio.fixture
async def get_from_redis(redis_client):
    async def inner(key: str):
        return await redis_client.get(key)

    return inner
