"""Strips configured secrets out of text before it leaves the server.

Adapter errors are surfaced to the browser so the demo can explain what
went wrong, and those strings interpolate upstream vendor responses. No
current code path puts an API key in one, but a vendor that echoes a
request header into an error body would leak it through that channel.
This is the last checkpoint before the response contract, so the
guarantee holds regardless of what a vendor decides to echo back.
"""
from api.config import settings

REDACTED = "[redacted]"

# Shortest string still worth treating as a secret. Guards against an
# env var set to "" or a single character blanking out normal text.
_MIN_SECRET_LENGTH = 8


def _configured_secrets() -> list[str]:
    return [
        value
        for value in (
            settings.NUTRIENT_DWS_API_KEY,
            settings.OPENAI_API_KEY,
            settings.UPSTASH_REDIS_REST_TOKEN,
        )
        if value and len(value) >= _MIN_SECRET_LENGTH
    ]


def redact_secrets(text: str) -> str:
    """Replaces any configured secret appearing in text with a marker."""
    for secret in _configured_secrets():
        text = text.replace(secret, REDACTED)
    return text
