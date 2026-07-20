from typing import Any
from datetime import datetime
from threading import Lock


class SharedContext:
    """A thread-safe shared memory space for all agents.
    
    This allows agents to share data with each other without
    direct communication. Think of it as a shared whiteboard
    that any agent can read from or write to.
    """
    
    def __init__(self):
        self._store: dict[str, Any] = {}
        self._metadata: dict[str, dict] = {}
        self._lock = Lock()
    
    def set(self, key: str, value: Any, author: str = "unknown") -> None:
        """Store a value in shared context."""
        with self._lock:
            self._store[key] = value
            self._metadata[key] = {
                "author": author,
                "updated_at": datetime.now().isoformat(),
            }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from shared context."""
        return self._store.get(key, default)
    
    def delete(self, key: str) -> bool:
        """Remove a value from shared context."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                del self._metadata[key]
                return True
            return False
    
    def list_keys(self) -> list[str]:
        """List all keys in shared context."""
        return list(self._store.keys())
    
    def get_metadata(self, key: str) -> dict | None:
        """Get metadata about when/who wrote a value."""
        return self._metadata.get(key)
    
    def clear(self) -> None:
        """Clear all shared context."""
        with self._lock:
            self._store.clear()
            self._metadata.clear()
    
    def __contains__(self, key: str) -> bool:
        return key in self._store
    
    def __len__(self) -> int:
        return len(self._store)
    
    def __repr__(self) -> str:
        return f"SharedContext(keys={self.list_keys()})"
