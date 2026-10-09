from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import time
import logging

from .config import settings
from .database import init_db
from .routers import auth_router, agents_router, tasks_router, websocket_router, execution_router, usage_router, organizations_router, marketplace_router, audit_router
from .services.metrics import metrics, generate_latest
from .services.cache import cache

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    init_db()
    logger.info("Database initialized")

    from .database import SessionLocal

    if settings.ENABLE_BILLING:
        from .services.usage import seed_billing_plans
        db = SessionLocal()
        try:
            seed_billing_plans(db)
            logger.info("Billing plans seeded")
        except Exception as e:
            logger.warning(f"Billing plan seeding skipped: {e}")
        finally:
            db.close()

    from .services.marketplace import seed_marketplace_templates
    db = SessionLocal()
    try:
        seed_marketplace_templates(db)
        logger.info("Marketplace templates seeded")
    except Exception as e:
        logger.warning(f"Marketplace seeding skipped: {e}")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade Multi-Agent Orchestration Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)


# ============================================================
# Middleware
# ============================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

# Trusted hosts (production)
if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect HTTP metrics."""
    start_time = time.time()
    
    # Add request ID
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    metrics.record_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.4f}"
    
    return response


# ============================================================
# Routes
# ============================================================

app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(tasks_router)
app.include_router(websocket_router)
app.include_router(execution_router)
app.include_router(usage_router)
app.include_router(organizations_router)
app.include_router(marketplace_router)
app.include_router(audit_router)


@app.get("/", tags=["System"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running"
    }


@app.get("/health", tags=["System"])
def health():
    """Health check endpoint."""
    from .database import check_db_health
    
    db_healthy = check_db_health()
    redis_healthy = cache.enabled  # optional: cache degrades gracefully without Redis

    status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": status,
        "checks": {
            "database": "ok" if db_healthy else "error",
            "redis": "ok" if redis_healthy else "unavailable",
        }
    }


@app.get("/metrics", tags=["System"])
def prometheus_metrics():
    """Prometheus metrics endpoint."""
    metrics.update_system_metrics()
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )


@app.get("/ready", tags=["System"])
def ready():
    """Readiness probe."""
    return {"ready": True}
