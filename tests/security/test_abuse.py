"""
Security & Abuse Simulation verification.
Section 14 — Malformed payloads, unauthorized access, spam flooding.
"""
import pytest
import uuid


@pytest.mark.asyncio
async def test_malformed_ingestion_payload_rejected(client):
    """Ingestion endpoint must reject missing required fields."""
    res = await client.post("/ingestion/mock", json={"complaint_text": "only text, nothing else"})
    assert res.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_missing_urgency_in_anonymous_report_rejected(client):
    """Anonymous report with missing urgency must fail validation."""
    res = await client.post("/api/incidents/anonymous", json={"category": "Security"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_unauthorized_settings_write_blocked(client):
    """Department Admin cannot write settings."""
    res = await client.post(
        "/api/settings",
        json={"critical_escalation_score": 50},
        headers={"x-user-role": "Department Admin"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_notification_injection_attempt_blocked(client):
    """Acknowledging a non-existent notification ID must return 404, not create it."""
    res = await client.post("/api/notifications/999999/acknowledge")
    assert res.status_code == 404

    # Verify no phantom notifications were created
    all_notifs = await client.get("/api/notifications")
    phantom = [n for n in all_notifs.json() if n["id"] == 999999]
    assert len(phantom) == 0


@pytest.mark.asyncio
async def test_spam_flood_ingestion_all_stored(client):
    """
    Spam flooding: inject 20 rapid complaints.
    All must be stored without data corruption.
    """
    spam_ids = []
    for _ in range(20):
        cid = f"SPAM-{uuid.uuid4().hex[:6].upper()}"
        spam_ids.append(cid)
        payload = {
            "complaint_id": cid,
            "source": "SpamFlood",
            "department": "General",
            "category": "Spam",
            "subcategory": "Test",
            "complaint_text": "This is a spam test complaint.",
            "sentiment_score": 0.0,
            "urgency_level": 1,
            "escalation_flag": "false",
            "resolved": "false",
            "duplicate_group_id": "",
            "toxicity_score": 5.0,
            "anonymous": "false",
            "response_delay_hours": "0",
        }
        await client.post("/ingestion/mock", json=payload)

    # Validate ingestion success rate target: > 99%
    feed = await client.get("/api/incidents/?limit=100")
    stored_ids = [c["complaint_id"] for c in feed.json()]
    matched = [cid for cid in spam_ids if cid in stored_ids]
    success_rate = len(matched) / len(spam_ids)
    assert success_rate >= 0.99, f"Ingestion success rate below target: {success_rate:.1%}"
