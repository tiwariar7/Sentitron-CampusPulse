"""
Notification Intelligence verification.
Section 14 — Lifecycle workflows, severity hierarchy, AI recommendations.
"""
import pytest
import uuid


async def create_notification(client, severity="WARNING", category="Operations"):
    """Helper — ingest a complaint that will trigger an escalation notification."""
    payload = {
        "complaint_id": f"NTF-{uuid.uuid4().hex[:6].upper()}",
        "source": "TestSuite",
        "department": "IT",
        "category": category,
        "subcategory": "Network",
        "complaint_text": "WiFi is completely down in block C.",
        "sentiment_score": -0.7,
        "urgency_level": 2,
        "escalation_flag": "true",  # Triggers WARNING notification
        "resolved": "false",
        "duplicate_group_id": "",
        "toxicity_score": 10.0,
        "anonymous": "false",
        "response_delay_hours": "0",
    }
    await client.post("/ingestion/mock", json=payload)
    notif_res = await client.get("/api/notifications/?state=CREATED")
    notifs = [n for n in notif_res.json() if n["title"] == "Automated Escalation"]
    return notifs[0] if notifs else None


@pytest.mark.asyncio
async def test_notification_lifecycle_acknowledge(client):
    """CREATED -> ACKNOWLEDGED transition must succeed."""
    notif = await create_notification(client)
    assert notif is not None
    res = await client.post(f"/api/notifications/{notif['id']}/acknowledge")
    assert res.status_code == 200
    assert res.json()["state"] == "ACKNOWLEDGED"


@pytest.mark.asyncio
async def test_notification_lifecycle_resolve(client):
    """CREATED -> RESOLVED transition must succeed."""
    notif = await create_notification(client)
    assert notif is not None
    res = await client.post(f"/api/notifications/{notif['id']}/resolve")
    assert res.status_code == 200
    assert res.json()["state"] == "RESOLVED"


@pytest.mark.asyncio
async def test_notification_lifecycle_dismiss(client):
    """CREATED -> DISMISSED transition must succeed."""
    notif = await create_notification(client)
    assert notif is not None
    res = await client.post(f"/api/notifications/{notif['id']}/dismiss")
    assert res.status_code == 200
    assert res.json()["state"] == "DISMISSED"


@pytest.mark.asyncio
async def test_nonexistent_notification_returns_404(client):
    res = await client.post("/api/notifications/99999/acknowledge")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_severity_filter_returns_only_matching(client):
    """Filtering by severity=HIGH must return only HIGH notifications."""
    res = await client.get("/api/notifications/?severity=HIGH")
    assert res.status_code == 200
    for notif in res.json():
        assert notif["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_critical_notification_has_ai_recommendation(client):
    """CRITICAL notifications (from anonymous Critical report) must attach AI recommendations."""
    payload = {"category": "Security", "description": "Fire alarm triggered near lab", "urgency": "Critical"}
    await client.post("/api/incidents/anonymous", json=payload)

    notif_res = await client.get("/api/notifications/?severity=CRITICAL")
    crits = notif_res.json()
    assert len(crits) >= 1
    assert crits[0]["ai_recommendations"] is not None
    assert "action" in crits[0]["ai_recommendations"]
