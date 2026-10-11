import hashlib
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.requests import Request as StarletteRequest

from ..config import settings
from ..services.cache import rate_limiter

EXEMPT_PATHS = {
    "/",
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}
AUTH_PATHS = {"/auth/login", "/auth/register"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-identity request limiting; in-memory or Redis via RateLimiter."""

    async def dispatch(
        self, request: StarletteRequest, call_next
    ) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if path in EXEMPT_PATHS:
            return await call_next(request)

        key, limit = self._key_and_limit(request, path)
        limited, retry_after = rate_limiter.check(
            key, max_requests=limit, window=settings.RATE_LIMIT_WINDOW
        )
        if limited:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)

    def _key_and_limit(self, request: StarletteRequest, path: str) -> tuple[str, int]:
        ip = request.client.host if request.client else "unknown"

        if path in AUTH_PATHS:
            return f"ip:{ip}", settings.RATE_LIMIT_AUTH_REQUESTS

        if settings.ENABLE_API_KEY_AUTH:
            api_key = request.headers.get(settings.API_KEY_HEADER)
            if api_key:
                digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
                return f"key:{digest}", settings.RATE_LIMIT_REQUESTS

        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                payload = jwt.decode(
                    auth[7:], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                sub = payload.get("sub")
                if sub:
                    return f"user:{sub}", settings.RATE_LIMIT_REQUESTS
            except JWTError:
                pass

        return f"ip:{ip}", settings.RATE_LIMIT_REQUESTS
