"""No-op KeyValueCache, never stores anything. Used for local dev with no Upstash creds."""


class NoopCache:
    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        return None
