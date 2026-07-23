from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import asyncio
import time
import logging

from .config import settings
from .database import init_db
from .api.v1.router import router as v1_router
from .services.metrics import metrics, generate_latest
from .domain.events import event_bus, Event, EventTypes
from .api.middleware import (
    RequestIDMiddleware,
    TimingMiddleware,
    RateLimitMiddleware,
    MetricsMiddleware,
    APIKeyAuthMiddleware,
    AuditLogMiddleware,
)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

timeout_worker_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global timeout_worker_task

    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    init_db()
    logger.info("Database initialized")

    if settings.ENABLE_BILLING:
        from .database import SessionLocal
        from .services.usage import seed_billing_plans
        db = SessionLocal()
        try:
            seed_billing_plans(db)
            logger.info("Billing plans seeded")
        except Exception as e:
            logger.warning(f"Billing plan seeding skipped: {e}")
        finally:
            db.close()

    from .workers.timeout import start_timeout_worker
    timeout_worker_task = asyncio.create_task(start_timeout_worker())
    logger.info("Timeout worker started")

    await event_bus.publish(Event(
        type=EventTypes.SYSTEM_STARTUP,
        data={"version": settings.VERSION, "environment": settings.ENVIRONMENT},
        source="main",
    ))

    yield

    if timeout_worker_task:
        timeout_worker_task.cancel()
        try:
            await timeout_worker_task
        except asyncio.CancelledError:
            pass
        logger.info("Timeout worker stopped")

    await event_bus.publish(Event(
        type=EventTypes.SYSTEM_SHUTDOWN,
        data={},
        source="main",
    ))
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade Multi-Agent Orchestration Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(AuditLogMiddleware)

if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )

app.add_middleware(APIKeyAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.TRUSTED_HOSTS,
    )

app.include_router(v1_router)

from .api.exceptions import global_exception_handler, validation_error_handler
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)


@app.get("/", tags=["System"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
    }


@app.get("/health", tags=["System"])
def health():
    from .database import check_db_health
    db_healthy = check_db_health()

    status = "healthy" if db_healthy else "degraded"

    return {
        "status": status,
        "checks": {
            "database": "ok" if db_healthy else "error",
        },
    }


@app.get("/metrics", tags=["System"])
def prometheus_metrics():
    metrics.update_system_metrics()
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )


@app.get("/ready", tags=["System"])
def ready():
    return {"ready": True}
