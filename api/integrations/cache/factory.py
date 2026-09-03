"""Factory: picks the active KeyValueCache from config."""
from functools import lru_cache

from api.config import settings
from api.integrations.cache.base import KeyValueCache
from api.integrations.cache.noop_adapter import NoopCache


@lru_cache
def get_cache() -> KeyValueCache:
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
        from api.integrations.cache.upstash_adapter import UpstashCache

        return UpstashCache()
    return NoopCache()
