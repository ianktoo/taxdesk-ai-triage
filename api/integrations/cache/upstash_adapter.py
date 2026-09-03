"""Upstash Redis adapter for the KeyValueCache capability.

Uses Upstash's REST API POST-with-command-array form (rather than the
rate limiter's GET-with-path-segments form) since cached values here
can be long base64 audio payloads that don't belong in a URL path.
"""
import httpx

from api.config import settings
from api.integrations.cache.base import CacheError


class UpstashCache:
    def __init__(self, rest_url: str | None = None, rest_token: str | None = None):
        self._rest_url = (rest_url or settings.UPSTASH_REDIS_REST_URL).rstrip("/")
        self._rest_token = rest_token or settings.UPSTASH_REDIS_REST_TOKEN
        if not self._rest_url or not self._rest_token:
            raise CacheError("Upstash REST URL/token are not configured")

    def _command(self, command: list[str]) -> dict:
        try:
            response = httpx.post(
                self._rest_url,
                headers={"Authorization": f"Bearer {self._rest_token}"},
                json=command,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise CacheError(f"Upstash request failed: {exc}") from exc

    def get(self, key: str) -> str | None:
        result = self._command(["GET", key])
        return result.get("result")

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._command(["SET", key, value, "EX", str(ttl_seconds)])
