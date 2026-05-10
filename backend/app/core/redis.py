import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

# Redis connection pool
_pool: redis.ConnectionPool | None = None
_client: redis.Redis | None = None


async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global _pool, _client
    _pool = redis.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=50,
        decode_responses=True,
    )
    _client = redis.Redis(connection_pool=_pool)
    await _client.ping()


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _client, _pool
    if _client:
        await _client.close()
    if _pool:
        await _pool.disconnect()


def get_redis() -> redis.Redis:
    """Get Redis client. Returns None if not initialized."""
    return _client


# --- Rate Limiting ---

async def check_rate_limit(user_id: str, limit: int = 60, window: int = 60) -> bool:
    """Check if user has exceeded rate limit. Returns True if allowed."""
    if not _client:
        return True
    key = f"rate_limit:{user_id}"
    current = await _client.get(key)
    if current and int(current) >= limit:
        return False
    await _client.incr(key)
    if not current:
        await _client.expire(key, window)
    return True


# --- SSE Pub/Sub (preparation for Phase 3 streaming) ---

async def publish_event(channel: str, event_type: str, data: dict) -> None:
    """Publish an SSE event to a Redis channel."""
    if not _client:
        return
    payload = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)
    await _client.publish(channel, payload)


async def subscribe_channel(channel: str) -> redis.client.PubSub:
    """Subscribe to a Redis channel for SSE events."""
    if not _client:
        return None
    pubsub = _client.pubsub()
    await pubsub.subscribe(channel)
    return pubsub


# --- Result Cache ---

async def cache_get(key: str) -> Any | None:
    """Get a cached value."""
    if not _client:
        return None
    val = await _client.get(f"cache:{key}")
    if val:
        return json.loads(val)
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set a cached value with TTL in seconds."""
    if not _client:
        return
    await _client.setex(
        f"cache:{key}",
        ttl,
        json.dumps(value, ensure_ascii=False),
    )
