"""Upstash Redis adapter for the RateLimiter capability.

Uses Upstash's REST API (no persistent connection needed, so it works
cleanly from stateless Vercel functions) to implement a fixed-window
counter per key: INCR key, and on the first hit in a window, EXPIRE it.
"""
import httpx

from api.config import settings
from api.integrations.rate_limit.base import RateLimitCheck, RateLimitError


class UpstashRateLimiter:
    def __init__(
        self,
        rest_url: str | None = None,
        rest_token: str | None = None,
        max_requests: int | None = None,
        window_seconds: int | None = None,
    ):
        self._rest_url = (rest_url or settings.UPSTASH_REDIS_REST_URL).rstrip("/")
        self._rest_token = rest_token or settings.UPSTASH_REDIS_REST_TOKEN
        self._max_requests = max_requests or settings.RATE_LIMIT_MAX_REQUESTS
        self._window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        if not self._rest_url or not self._rest_token:
            raise RateLimitError("Upstash REST URL/token are not configured")

    def _command(self, *parts: str) -> dict:
        path = "/".join(parts)
        try:
            response = httpx.get(
                f"{self._rest_url}/{path}",
                headers={"Authorization": f"Bearer {self._rest_token}"},
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise RateLimitError(f"Upstash request failed: {exc}") from exc

    def check(self, key: str) -> RateLimitCheck:
        redis_key = f"ratelimit:{key}"
        count = self._command("incr", redis_key)["result"]

        if count == 1:
            self._command("expire", redis_key, str(self._window_seconds))

        ttl_result = self._command("ttl", redis_key)["result"]
        reset_seconds = ttl_result if ttl_result and ttl_result > 0 else self._window_seconds

        allowed = count <= self._max_requests
        remaining = max(self._max_requests - count, 0)
        return RateLimitCheck(
            allowed=allowed,
            limit=self._max_requests,
            remaining=remaining,
            reset_seconds=reset_seconds,
            window_seconds=self._window_seconds,
        )
