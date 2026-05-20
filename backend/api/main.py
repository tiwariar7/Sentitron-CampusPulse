from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
import time
import uuid
import logging

from starlette.requests import Request
from starlette.responses import Response

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import engine, Base
from ingestion.mock_ingestion import router as ingestion_router
from ws_manager.manager import SYSTEM_METRICS

logger = logging.getLogger(__name__)

# ── Prometheus instrumentation (lazy: skip if package missing) ───
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    _PROMETHEUS_ENABLED = True
except ImportError:
    _PROMETHEUS_ENABLED = False
    logger.warning("prometheus-fastapi-instrumentator not installed — /metrics disabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── DB schema init ──────────────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Kafka producer pool ─────────────────────────────────────
    try:
        from ingestion.kafka_producer import KafkaProducerManager
        await KafkaProducerManager.get_producer()
    except Exception as e:
        logger.warning(f"Kafka broker unavailable, using inline fallback mode: {e}")

    # ── Seed default admin ──────────────────────────────────────
    try:
        from services.db import AsyncSessionLocal, User
        from services.auth import hash_password
        from sqlalchemy.future import select
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.username == "admin"))
            if not result.scalars().first():
                default_admin = User(
                    username="admin",
                    email="admin@sentitron.ai",
                    hashed_password=hash_password("adminpassword"),
                    role="admin",
                    department="General"
                )
                session.add(default_admin)
                await session.commit()
                logger.info("Seeded default Admin user (admin / adminpassword)")
    except Exception as e:
        logger.error(f"Failed to seed default Admin: {e}")

    yield

    # ── Shutdown ────────────────────────────────────────────────
    try:
        from ingestion.kafka_producer import KafkaProducerManager
        await KafkaProducerManager.close_producer()
    except Exception as e:
        logger.warning(f"Kafka shutdown error: {e}")

    try:
        from services.redis_cache import redis_cache
        await redis_cache.close()
    except Exception:
        pass

    await engine.dispose()


app = FastAPI(
    title="Sentitron CampusPulse API",
    description="Real-Time AI Campus Intelligence & Escalation Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Prometheus metrics (/metrics) ───────────────────────────────
if _PROMETHEUS_ENABLED:
    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ── Correlation ID + Latency Telemetry ──────────────────────────
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next) -> Response:
    # Propagate or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    start_time     = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000.0

    # Track rolling latency for /api/monitoring/metrics
    SYSTEM_METRICS["api_latencies"].append(duration_ms)
    if len(SYSTEM_METRICS["api_latencies"]) > 50:
        SYSTEM_METRICS["api_latencies"].pop(0)
    SYSTEM_METRICS["total_requests"] += 1

    response.headers["X-Correlation-ID"]      = correlation_id
    response.headers["X-API-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response

# ── Security Headers ─────────────────────────────────────────────
from middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# ── CORS ─────────────────────────────────────────────────────────
_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiter ─────────────────────────────────────────────────
try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from middleware.rate_limiter import limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except ImportError:
    logger.warning("slowapi not installed — rate limiting disabled")

# ── Routers ──────────────────────────────────────────────────────
from api.routers.auth         import router as auth_router
from api.routers.incidents    import router as incidents_router
from api.routers.clusters     import router as clusters_router
from api.routers.analytics    import router as analytics_router
from api.routers.monitoring   import router as monitoring_router
from api.routers.forecasting  import router as forecasting_router
from api.routers.settings     import router as settings_router
from api.routers.notifications import router as notifications_router

app.include_router(auth_router)
app.include_router(ingestion_router)
app.include_router(incidents_router)
app.include_router(clusters_router)
app.include_router(analytics_router)
app.include_router(monitoring_router)
app.include_router(forecasting_router)
app.include_router(settings_router)
app.include_router(notifications_router)


# ── Health / Probe Endpoints ─────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health_check():
    """Basic health check — always 200 if process is alive."""
    return {"status": "ok", "service": "CampusPulse Backend", "version": "2.0.0"}


@app.get("/livez", tags=["ops"])
async def liveness():
    """Kubernetes liveness probe — returns 200 if process is alive."""
    return {"status": "alive"}


@app.get("/readyz", tags=["ops"])
async def readiness():
    """
    Kubernetes readiness probe.
    Checks DB and Redis connectivity. Returns 503 if any critical dependency is down.
    """
    checks = {}

    # DB check
    try:
        from services.db import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        from services.redis_cache import redis_cache
        alive = await redis_cache.ping()
        checks["redis"] = "ok" if alive else "unavailable"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    is_ready = checks["database"] == "ok"
    status_code = 200 if is_ready else 503
    return Response(
        content=str({"status": "ready" if is_ready else "not_ready", "checks": checks}),
        status_code=status_code,
        media_type="application/json",
    )


@app.get("/api/monitoring/models", tags=["monitoring"])
async def get_model_registry():
    """Admin: view active AI model versions."""
    from services.model_registry import get_all_models
    from services.auth import RoleChecker, User
    return get_all_models()


# ── WebSocket Endpoints ──────────────────────────────────────────
from ws_manager.manager import manager, notification_manager


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/notifications")
async def websocket_notifications_endpoint(websocket: WebSocket):
    await notification_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
