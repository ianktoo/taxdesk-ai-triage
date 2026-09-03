"""Per-IP demo throttling for the expensive routes (triage, approve).

No login required: keys the RateLimiter capability off the client IP
(preferring X-Forwarded-For, since Vercel sits behind a proxy).
"""
from fastapi import Request

from api.integrations.rate_limit.factory import get_rate_limiter


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _humanize(seconds: int) -> str:
    if seconds < 60:
        return "1 second" if seconds == 1 else f"{seconds} seconds"
    minutes = round(seconds / 60)
    return "1 minute" if minutes == 1 else f"{minutes} minutes"


def check_rate_limit(request: Request) -> dict | None:
    """Returns an {ok:false,error} dict if the caller is over quota, else None."""
    limiter = get_rate_limiter()
    result = limiter.check(client_ip(request))
    if result.allowed:
        return None

    # The quota and the wait are two different numbers, and saying
    # "N requests per <seconds remaining>" reads as a quota that shrinks
    # every time you retry. Report the window for the quota and the TTL
    # for the wait.
    quota = f"{result.limit} requests per {_humanize(result.window_seconds)}"
    wait = f"Try again in about {_humanize(result.reset_seconds)}."
    return {"ok": False, "error": f"Demo limit reached ({quota}). {wait}"}
