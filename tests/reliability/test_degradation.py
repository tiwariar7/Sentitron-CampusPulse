"""
Reliability & Failure Handling verification.
Section 12 — Graceful degradation, DLQ fallback, recovery validation.
"""
import pytest
import uuid


@pytest.mark.asyncio
async def test_monitoring_metrics_always_return(client):
    """Monitoring endpoint must return metrics even under simulated load."""
    for _ in range(5):
        res = await client.get("/api/monitoring/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "gpu_utilization" in data
        assert "inference_latency_ms" in data
        assert "kafka_throughput_sec" in data


@pytest.mark.asyncio
async def test_forecasting_always_returns_valid_range(client):
    """Forecasting must always return a surge_risk_probability in a valid numeric range."""
    for _ in range(5):
        res = await client.get("/api/forecasting/trends")
        assert res.status_code == 200
        data = res.json()
        risk = data["surge_risk_probability"]
        confidence = data["confidence"]
        assert 0 <= risk <= 100, f"Invalid risk value: {risk}"
        assert 0 <= confidence <= 100, f"Invalid confidence value: {confidence}"
        assert data["predicted_cluster"] != ""


@pytest.mark.asyncio
async def test_notification_state_persists_after_action(client):
    """Once acknowledged, a notification state must remain ACKNOWLEDGED on re-fetch."""
    # Create notification via escalated complaint
    cid = f"REL-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "complaint_id": cid, "source": "Reliability", "department": "IT",
        "category": "Network", "subcategory": "WiFi",
        "complaint_text": "Persistent connectivity failure in lab.",
        "sentiment_score": -0.5, "urgency_level": 3,
        "escalation_flag": "true", "resolved": "false",
        "duplicate_group_id": "", "toxicity_score": 10.0,
        "anonymous": "false", "response_delay_hours": "0",
    }
    await client.post("/ingestion/mock", json=payload)

    notif_res = await client.get("/api/notifications/?state=CREATED")
    created = [n for n in notif_res.json() if n["title"] == "Automated Escalation"]
    assert len(created) >= 1
    notif_id = created[0]["id"]

    # Acknowledge it
    await client.post(f"/api/notifications/{notif_id}/acknowledge")

    # Re-fetch and confirm it's now ACKNOWLEDGED
    all_notifs = await client.get("/api/notifications")
    target = next((n for n in all_notifs.json() if n["id"] == notif_id), None)
    assert target is not None
    assert target["lifecycle_state"] == "ACKNOWLEDGED"
