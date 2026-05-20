from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import engine, Base
from ingestion.mock_ingestion import router as ingestion_router
from ws_manager.manager import SYSTEM_METRICS

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQL database schema on start
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Shared Kafka connection pool
    try:
        from ingestion.kafka_producer import KafkaProducerManager
        await KafkaProducerManager.get_producer()
    except Exception as e:
        print(f"FastAPI Start: Kafka broker unavailable, running with inline processing fallback mode. ({e})")
        
# Seed default admin user if none exists
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
                print("FastAPI Start: Seeded default Admin user (admin / adminpassword)")
    except Exception as e:
        print(f"FastAPI Start: Failed to seed default Admin: {e}")
        
    yield
    
    # Dispose Shared Kafka connection pool
    try:
        from ingestion.kafka_producer import KafkaProducerManager
        await KafkaProducerManager.close_producer()
    except Exception as e:
        print(f"FastAPI Shutdown: Failed to release Kafka resources: {e}")
        
    await engine.dispose()

app = FastAPI(
    title="Sentitron CampusPulse API",
    description="Real-Time AI Campus Intelligence & Escalation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Latency Telemetry Middleware
@app.middleware("http")
async def track_latency_middleware(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    
    # Store dynamic running metrics in shared memory module
    SYSTEM_METRICS["api_latencies"].append(duration_ms)
    if len(SYSTEM_METRICS["api_latencies"]) > 50:
        SYSTEM_METRICS["api_latencies"].pop(0)
    SYSTEM_METRICS["total_requests"] += 1
    
    response.headers["X-API-Process-Time-Ms"] = str(duration_ms)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
from api.routers.auth import router as auth_router
from api.routers.incidents import router as incidents_router
from api.routers.clusters import router as clusters_router
from api.routers.analytics import router as analytics_router
from api.routers.monitoring import router as monitoring_router
from api.routers.forecasting import router as forecasting_router
from api.routers.settings import router as settings_router
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

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "CampusPulse Backend"}

from fastapi import WebSocket, WebSocketDisconnect
from ws_manager.manager import manager, notification_manager

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # keep alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/notifications")
async def websocket_notifications_endpoint(websocket: WebSocket):
    await notification_manager.connect(websocket)
    try:
        while True:
            # keep alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)
