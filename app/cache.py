import time
from typing import Any, Callable


class TTLCache:
    """Minimal in-process TTL cache, replacement for Streamlit's @st.cache_data."""

    def __init__(self, ttl_seconds: float):
        self.ttl_seconds = ttl_seconds
        self._store: dict[Any, tuple[float, Any]] = {}

    def get_or_set(self, key: Any, factory: Callable[[], Any]) -> Any:
        now = time.monotonic()
        cached = self._store.get(key)
        if cached is not None and cached[0] > now:
            return cached[1]
        value = factory()
        self._store[key] = (now + self.ttl_seconds, value)
        return value

    async def aget_or_set(self, key: Any, factory: Callable[[], Any]) -> Any:
        now = time.monotonic()
        cached = self._store.get(key)
        if cached is not None and cached[0] > now:
            return cached[1]
        value = await factory()
        self._store[key] = (now + self.ttl_seconds, value)
        return value

    def clear(self) -> None:
        self._store.clear()


library_cache = TTLCache(ttl_seconds=1800)
search_cache = TTLCache(ttl_seconds=1800)
model_cache = TTLCache(ttl_seconds=3600)
