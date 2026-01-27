"""
Redis package for cache and session store.
Provides in-memory speed, data structure support, and pub/sub capabilities.
"""
from .config import RedisConfig, redis_config
from .redis_client import RedisClient

def get_redis_client():
    return RedisClient()

__all__ = [
    "RedisConfig",
    "redis_config",
    "RedisClient",
    "get_redis_client",
]

