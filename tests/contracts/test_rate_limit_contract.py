from api.integrations.rate_limit.noop_adapter import NoopRateLimiter


def test_noop_limiter_satisfies_rate_limit_contract():
    limiter = NoopRateLimiter()
    result = limiter.check("1.2.3.4")

    assert result.allowed is True
    assert result.remaining >= 0
