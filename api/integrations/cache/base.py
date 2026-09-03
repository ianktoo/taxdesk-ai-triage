"""Contract for the KeyValueCache capability.

Used to avoid regenerating expensive AI output (generated personas,
synthesized speech) for the same input twice. Values are opaque
base64-safe strings, callers encode/decode their own payloads.
"""
from typing import Protocol, runtime_checkable


class CacheError(Exception):
    """Normalized error for the KeyValueCache capability."""


@runtime_checkable
class KeyValueCache(Protocol):
    def get(self, key: str) -> str | None:
        """Returns the cached value for `key`, or None if not present."""
        ...

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Stores `value` under `key`, expiring after `ttl_seconds`."""
        ...
