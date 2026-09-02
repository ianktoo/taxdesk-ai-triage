"""The one response contract used at every interface boundary."""
from typing import Any


def ok(data: Any) -> dict:
    return {"ok": True, "data": data}


def err(error: str) -> dict:
    return {"ok": False, "error": error}
