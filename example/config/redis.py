import aioredis
from .settings import REDIS_URL
from aioredis.client import Redis


async def get_redis() -> Redis:
    client: Redis = await aioredis.from_url(REDIS_URL)
    yield client
    await client.close()
