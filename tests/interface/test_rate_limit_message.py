"""The over-quota message has to state two different numbers correctly.

`limit` applies to the whole window; `reset_seconds` counts down. Saying
"N requests per <seconds remaining>" reads as a quota that shrinks every
time the caller retries, which is what this guards against.
"""
from types import SimpleNamespace

import pytest

from api.integrations.rate_limit.base import RateLimitCheck
from api.interface import rate_limit_guard
from api.interface.rate_limit_guard import _humanize, check_rate_limit


class StubLimiter:
    def __init__(self, check: RateLimitCheck):
        self._check = check

    def check(self, key: str) -> RateLimitCheck:
        return self._check


def fake_request():
    return SimpleNamespace(headers={}, client=SimpleNamespace(host="1.2.3.4"))


@pytest.fixture
def limiter(monkeypatch):
    def install(check: RateLimitCheck):
        monkeypatch.setattr(rate_limit_guard, "get_rate_limiter", lambda: StubLimiter(check))

    return install


def test_allowed_request_passes_through(limiter):
    limiter(RateLimitCheck(allowed=True, limit=30, remaining=29, reset_seconds=300, window_seconds=300))

    assert check_rate_limit(fake_request()) is None


def test_blocked_request_reports_quota_and_wait_separately(limiter):
    limiter(RateLimitCheck(allowed=False, limit=30, remaining=0, reset_seconds=112, window_seconds=300))

    error = check_rate_limit(fake_request())

    assert error["ok"] is False
    assert "30 requests per 5 minutes" in error["error"]
    assert "Try again in about 2 minutes" in error["error"]
    # The countdown must never be presented as the quota period.
    assert "30 requests per 2 minutes" not in error["error"]


@pytest.mark.parametrize(
    "seconds,expected",
    [(1, "1 second"), (45, "45 seconds"), (60, "1 minute"), (112, "2 minutes"), (300, "5 minutes")],
)
def test_humanize_reads_naturally(seconds, expected):
    assert _humanize(seconds) == expected
