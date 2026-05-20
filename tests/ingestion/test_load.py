"""
Load & Concurrency verification.
Section 3 — Concurrent ingestion burst, throughput, success rate.
"""
import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport

import os, sys
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api.main import app


async def push_complaint(client: AsyncClient, cid: str) -> bool:
    payload = {
        "complaint_id": cid, "source": "LoadTest", "department": "IT",
        "category": "Infrastructure", "subcategory": "Network",
        "complaint_text": f"Load test complaint {cid}",
        "sentiment_score": -0.3, "urgency_level": 2,
        "escalation_flag": "false", "resolved": "false",
        "duplicate_group_id": "", "toxicity_score": 5.0,
        "anonymous": "false", "response_delay_hours": "0",
    }
    try:
        res = await client.post("/ingestion/mock", json=payload, timeout=10.0)
        return res.status_code == 200
    except Exception:
        return False


@pytest.mark.asyncio
async def test_concurrent_ingestion_burst_100(client):
    """
    MVP Load Test: 100 concurrent ingestion requests.
    Target: > 99% success rate, < 300ms avg latency.
    """
    batch_size = 100
    ids = [f"LOAD-{uuid.uuid4().hex[:8].upper()}" for _ in range(batch_size)]

    import time
    start = time.monotonic()
    results = await asyncio.gather(*[push_complaint(client, cid) for cid in ids])
    elapsed = time.monotonic() - start

    success_count = sum(results)
    success_rate = success_count / batch_size
    avg_latency_ms = (elapsed / batch_size) * 1000

    print(f"\nLoad Test — {batch_size} concurrent: {success_count}/{batch_size} OK "
          f"({success_rate:.1%}) | avg {avg_latency_ms:.0f}ms")

    assert success_rate >= 0.99, f"Success rate below 99%: {success_rate:.1%}"
    assert avg_latency_ms < 300, f"Avg latency above 300ms: {avg_latency_ms:.0f}ms"


@pytest.mark.asyncio
async def test_concurrent_notification_reads_stable(client):
    """
    WebSocket fanout smoke: 25 simultaneous GET /api/notifications.
    All must return 200 with no errors.
    """
    async def fetch(c):
        res = await c.get("/api/notifications", timeout=5.0)
        return res.status_code == 200

    results = await asyncio.gather(*[fetch(client) for _ in range(25)])
    assert all(results), f"Some notification fetches failed: {results.count(False)} failures"
