"""The one response contract used at every interface boundary."""
from typing import Any

from api.utils.redaction import redact_secrets


def ok(data: Any) -> dict:
    return {"ok": True, "data": data}


def err(error: str) -> dict:
    # Redacted here rather than at each call site: error strings carry
    # interpolated vendor responses, and this is the single chokepoint
    # every error passes through on its way to a client.
    return {"ok": False, "error": redact_secrets(error)}
