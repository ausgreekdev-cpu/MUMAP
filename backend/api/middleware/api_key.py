from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

from ...config import settings
from ...database import SessionLocal
from ...repositories.user_repo import UserRepository
logger = logging.getLogger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = [
        "/",
        "/health",
        "/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/",
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.ENABLE_API_KEY_AUTH:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(ep) for ep in self.EXCLUDED_PATHS):
            return await call_next(request)

        if request.headers.get("Authorization"):
            return await call_next(request)

        api_key = request.headers.get(settings.API_KEY_HEADER)
        if not api_key:
            return await call_next(request)

        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            user = user_repo.get_by_api_key(api_key)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled",
                )

            request.state.user = user
            request.state.auth_method = "api_key"

        finally:
            db.close()

        return await call_next(request)
