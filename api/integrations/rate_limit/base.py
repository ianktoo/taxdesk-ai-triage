"""Contract for the RateLimiter capability.

Anything that can answer "has this key used up its quota in the
current window?" implements this Protocol (Upstash Redis, a no-op
for local dev, or something else later). Services and routes must
only ever depend on this interface.
"""
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class RateLimitCheck:
    allowed: bool
    limit: int
    remaining: int
    # Seconds until the current window resets, i.e. how long a blocked
    # caller must wait. Distinct from window_seconds: this one counts
    # down, and is what a "try again in N" message needs.
    reset_seconds: int
    # Length of the whole window, i.e. the period `limit` applies to.
    window_seconds: int = 0


class RateLimitError(Exception):
    """Normalized error for the RateLimiter capability."""


@runtime_checkable
class RateLimiter(Protocol):
    def check(self, key: str) -> RateLimitCheck:
        """Record one hit for `key` and report whether it is still within quota."""
        ...
