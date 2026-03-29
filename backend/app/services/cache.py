import json
from collections.abc import Callable, Coroutine
from typing import Any

from redis.asyncio import Redis

STATUSES_KEY = "ref:statuses"
PRIORITIES_KEY = "ref:priorities"
EMPLOYEES_KEY = "ref:employees"
REF_TTL = 600  # 10 min
EMPLOYEES_TTL = 300  # 5 min


async def get_cached(redis: Redis, key: str) -> Any | None:
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def set_cached(redis: Redis, key: str, value: Any, ttl: int) -> None:
    await redis.set(key, json.dumps(value), ex=ttl)


async def invalidate(redis: Redis, *keys: str) -> None:
    if keys:
        await redis.delete(*keys)


async def cached(
    redis: Redis,
    key: str,
    ttl: int,
    loader: Callable[[], Coroutine[Any, Any, Any]],
) -> Any:
    data = await get_cached(redis, key)
    if data is not None:
        return data
    data = await loader()
    await set_cached(redis, key, data, ttl)
    return data
