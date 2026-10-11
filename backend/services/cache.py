import json
import hashlib
import threading
import time
from typing import Any, Optional, Callable
from functools import wraps
from datetime import timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from ..config import settings


class RedisCache:
    """Redis-based caching with TTL support."""
    
    def __init__(self):
        if not REDIS_AVAILABLE:
            self.client = None
            self.enabled = False
            return
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.client.ping()
            self.enabled = True
        except Exception:
            self.client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.enabled:
            return False
        try:
            ttl = ttl or settings.CACHE_TTL
            self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.enabled:
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter."""
        if not self.enabled:
            return None
        try:
            return self.client.incr(key, amount)
        except Exception:
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key."""
        if not self.enabled:
            return False
        try:
            self.client.expire(key, ttl)
            return True
        except Exception:
            return False


class RateLimiter:
    """Fixed-window rate limiter: Redis when available, in-memory otherwise."""

    _memory_lock = threading.Lock()
    _memory_windows: dict[str, tuple[float, int]] = {}

    def __init__(self):
        self.cache = RedisCache()

    def _memory_hit(
        self, key: str, max_requests: int, window: int
    ) -> tuple[bool, float]:
        """Record one hit; return (limited, retry_after_seconds)."""
        now = time.monotonic()
        with RateLimiter._memory_lock:
            stored = RateLimiter._memory_windows.get(key)
            if stored is None or now - stored[0] >= window:
                start, count = now, 1
            else:
                start, count = stored
                count += 1
            RateLimiter._memory_windows[key] = (start, count)
            if len(RateLimiter._memory_windows) > 5000:
                RateLimiter._memory_windows = {
                    k: v
                    for k, v in RateLimiter._memory_windows.items()
                    if now - v[0] < window
                }
        retry_after = max(1, int(window - (now - start)))
        return count > max_requests, retry_after

    def is_rate_limited(
        self,
        key: str,
        max_requests: int = None,
        window: int = None,
    ) -> bool:
        """Check if request should be rate limited."""
        max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_WINDOW

        if self.cache.enabled:
            try:
                current = self.cache.increment(f"ratelimit:{key}")
                if current == 1:
                    self.cache.expire(f"ratelimit:{key}", window)
                return current > max_requests
            except Exception:
                return False

        limited, _ = self._memory_hit(key, max_requests, window)
        return limited

    def check(self, key: str, max_requests: int = None, window: int = None):
        """Return (limited, retry_after_seconds)."""
        max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_WINDOW

        if self.cache.enabled:
            return self.is_rate_limited(key, max_requests, window), window

        return self._memory_hit(key, max_requests, window)

    def get_remaining(self, key: str, max_requests: int = None, window: int = None) -> int:
        """Get remaining requests in current window."""
        max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        window = window or settings.RATE_LIMIT_WINDOW

        if self.cache.enabled:
            current = self.cache.get(f"ratelimit:{key}")
            return max(0, max_requests - (current or 0))

        now = time.monotonic()
        with RateLimiter._memory_lock:
            stored = RateLimiter._memory_windows.get(key)
            if stored is None or now - stored[0] >= window:
                return max_requests
            return max(0, max_requests - stored[1])


def rate_limit(max_requests: int = None, window: int = None):
    """Decorator for rate limiting endpoints."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import Request, HTTPException
            
            # Get request from args (FastAPI injects it)
            request = None
            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                    break
            
            if request and settings.RATE_LIMIT_ENABLED:
                # Use IP + endpoint as key
                client_ip = request.client.host if request.client else "unknown"
                key = f"{client_ip}:{func.__name__}"
                
                limiter = RateLimiter()
                if limiter.is_rate_limited(key, max_requests, window):
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Please try again later."
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global instances
cache = RedisCache()
rate_limiter = RateLimiter()
