import time
from typing import Any, Optional


class Cache:
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self._store: dict[str, tuple[Any, float]] = {}
        self.enabled = True
        self.default_ttl = default_ttl
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        if len(self._store) >= self.max_size:
            self._evict()
        expire = time.time() + (ttl or self.default_ttl)
        self._store[key] = (value, expire)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def get_or_set(self, key: str, factory, ttl: int = None) -> Any:
        val = self.get(key)
        if val is not None:
            return val
        val = factory()
        self.set(key, val, ttl)
        return val

    def _evict(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if exp and now > exp]
        for k in expired:
            del self._store[k]
        if len(self._store) >= self.max_size:
            oldest = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest]


cache = Cache()
