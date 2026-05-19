from fastapi import FastAPI
from contextlib import asynccontextmanager
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import engine, Base
from ingestion.mock_ingestion import router as ingestion_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    async with engine.begin() as conn:
        # In a production environment, use Alembic for migrations instead
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown
    await engine.dispose()

app = FastAPI(
    title="Sentitron CampusPulse API",
    description="Real-Time AI Campus Intelligence & Escalation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Include Routers
app.include_router(ingestion_router)

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "CampusPulse Backend"}
