"""Factory: picks the active RateLimiter from config.

Falls back to the no-op limiter automatically when Upstash creds
aren't set, so local dev needs no extra setup.
"""
from functools import lru_cache

from api.config import settings
from api.integrations.rate_limit.base import RateLimiter
from api.integrations.rate_limit.noop_adapter import NoopRateLimiter


@lru_cache
def get_rate_limiter() -> RateLimiter:
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
        from api.integrations.rate_limit.upstash_adapter import UpstashRateLimiter

        return UpstashRateLimiter()
    return NoopRateLimiter()
