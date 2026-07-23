from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time

logger = logging.getLogger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    AUDIT_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
    AUDIT_PATHS = ["/api/v1/"]

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in self.AUDIT_METHODS:
            return await call_next(request)

        if not any(request.url.path.startswith(p) for p in self.AUDIT_PATHS):
            return await call_next(request)

        start_time = time.time()

        body = None
        try:
            body = await request.body()
        except Exception:
            pass

        response = await call_next(request)

        duration = time.time() - start_time

        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.id

        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        logger.info(
            f"AUDIT: {request.method} {request.url.path} "
            f"| user={user_id} | status={response.status_code} "
            f"| duration={duration:.4f}s | ip={client_ip}"
        )

        return response
