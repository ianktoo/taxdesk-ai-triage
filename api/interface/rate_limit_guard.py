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


def check_rate_limit(request: Request) -> dict | None:
    """Returns an {ok:false,error} dict if the caller is over quota, else None."""
    limiter = get_rate_limiter()
    result = limiter.check(client_ip(request))
    if result.allowed:
        return None
    return {
        "ok": False,
        "error": (
            f"Demo limit reached ({result.limit} requests per "
            f"{result.reset_seconds}s). Please try again shortly."
        ),
    }
