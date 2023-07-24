from redis.asyncio import Redis
from .settings import REDIS_URL


async def get_redis() -> Redis:
    client: Redis = await Redis.from_url(REDIS_URL)
    yield client
    await client.close()
