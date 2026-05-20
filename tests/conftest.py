"""
Root conftest.py — shared fixtures for the entire test suite.
Uses a persistent file-based SQLite test database for the full session.
"""
import os
import sys

# --- Path bootstrap (must precede all backend imports) ---
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")

for _p in (_PROJECT_ROOT, _BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Isolated test DB — file-based so tables persist across the session
_TEST_DB_PATH = os.path.join(_PROJECT_ROOT, "test_campuspulse.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# --- Import app AFTER setting DATABASE_URL so the engine picks it up ---
from api.main import app
from services.db import engine, Base


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Create all DB tables at session start.
    The app's own lifespan also calls create_all, which is idempotent — no conflict.
    Tables are NOT dropped mid-session; only cleaned up after all tests finish.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup: drop all tables and close engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    # Remove the test DB file (Windows may hold a lock briefly)
    import asyncio as _asyncio
    await _asyncio.sleep(0.2)
    try:
        if os.path.exists(_TEST_DB_PATH):
            os.remove(_TEST_DB_PATH)
    except PermissionError:
        pass  # Windows file lock; file will be cleaned up on next run


@pytest_asyncio.fixture
async def client(setup_test_db):
    """
    HTTPX async client wrapping the FastAPI ASGI app.
    follow_redirects=True handles FastAPI's trailing-slash 307 redirects.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac
