from typing import AsyncGenerator

from decouple import config
from redis.asyncio import ConnectionPool, Redis

REDIS_HOST = config("VALKEY_HOST", default="valkey")
REDIS_PORT = config("VALKEY_PORT", default=6379, cast=int)
REDIS_DB = config("VALKEY_DB", default=0, cast=int)

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Create Connection Pool
pool = ConnectionPool.from_url(REDIS_URL)


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency Injection for Redis connection
    """

    client = Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()
