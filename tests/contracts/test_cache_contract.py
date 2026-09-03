from api.integrations.cache.noop_adapter import NoopCache


def test_noop_cache_satisfies_key_value_cache_contract():
    cache = NoopCache()
    cache.set("some-key", "some-value", ttl_seconds=60)

    assert cache.get("some-key") is None
