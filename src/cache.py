import time
from typing import Any, Dict, Tuple

class TTLCache:
    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_s: int) -> None:
        self._store[key] = (time.time() + ttl_s, value)

CACHE = TTLCache()
