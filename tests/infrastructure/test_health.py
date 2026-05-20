"""
Infrastructure verification.
Section 1 — Service health and environment validation.
"""
import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "CampusPulse Backend"


@pytest.mark.asyncio
async def test_api_latency_within_target(client):
    """API latency target: < 300ms"""
    import time
    start = time.monotonic()
    response = await client.get("/health")
    elapsed_ms = (time.monotonic() - start) * 1000
    assert response.status_code == 200
    assert elapsed_ms < 300, f"Health endpoint too slow: {elapsed_ms:.1f}ms"


@pytest.mark.asyncio
async def test_notifications_endpoint_reachable(client):
    response = await client.get("/api/notifications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_settings_endpoint_reachable(client):
    response = await client.get("/api/settings", headers={"x-user-role": "Super Admin"})
    assert response.status_code == 200
