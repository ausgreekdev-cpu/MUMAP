import time
from collections import defaultdict
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, client_id: str, now: float) -> None:
        cutoff = now - self.window_seconds
        self._requests[client_id] = [
            ts for ts in self._requests[client_id] if ts > cutoff
        ]

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        if not self._is_rate_limited_path(request.url.path):
            return await call_next(request)

        client_id = self._get_client_id(request)
        now = time.time()

        self._clean_old_requests(client_id, now)

        if len(self._requests[client_id]) >= self.requests_per_minute:
            retry_after = int(self.window_seconds - (now - self._requests[client_id][0]))
            logger.warning(f"Rate limit exceeded for client {client_id}")

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after)),
                },
            )

        self._requests[client_id].append(now)

        response = await call_next(request)

        remaining = self.requests_per_minute - len(self._requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))

        return response

    def _is_rate_limited_path(self, path: str) -> bool:
        excluded_paths = ["/health", "/ready", "/metrics", "/docs", "/openapi.json"]
        return not any(path.startswith(ep) for ep in excluded_paths)
