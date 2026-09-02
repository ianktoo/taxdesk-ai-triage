"""No-op RateLimiter, always allows. Used for local dev with no Upstash creds."""
from api.integrations.rate_limit.base import RateLimitCheck


class NoopRateLimiter:
    def check(self, key: str) -> RateLimitCheck:
        return RateLimitCheck(allowed=True, limit=0, remaining=0, reset_seconds=0)
