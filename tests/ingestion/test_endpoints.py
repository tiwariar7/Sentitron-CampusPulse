"""
Ingestion & Intelligence Trigger verification.
Sections 3, 6, 14 — Ingestion endpoints, event-driven notifications,
toxicity + escalation thresholds, data quality.
"""
import pytest
import uuid


def make_complaint(toxicity=10.0, escalation="false", urgency=2, cluster=""):
    return {
        "complaint_id": f"TST-{uuid.uuid4().hex[:6].upper()}",
        "source": "TestSuite",
        "department": "Hostel",
        "category": "Maintenance",
        "subcategory": "Plumbing",
        "complaint_text": "Water is leaking from the ceiling in block B.",
        "sentiment_score": -0.5,
        "urgency_level": urgency,
        "escalation_flag": escalation,
        "resolved": "false",
        "duplicate_group_id": cluster,
        "toxicity_score": toxicity,
        "anonymous": "false",
        "response_delay_hours": "0",
    }


@pytest.mark.asyncio
async def test_ingestion_stores_complaint(client):
    """Ingested complaint must appear in /api/incidents."""
    payload = make_complaint()
    res = await client.post("/ingestion/mock", json=payload)
    assert res.status_code == 200
    assert res.json()["complaint_id"] == payload["complaint_id"]

    feed = await client.get("/api/incidents")
    ids = [c["complaint_id"] for c in feed.json()]
    assert payload["complaint_id"] in ids


@pytest.mark.asyncio
async def test_toxicity_spike_triggers_notification(client):
    """A complaint with toxicity > 70 must generate a HIGH notification."""
    # Ensure threshold is 70
    headers = {"x-user-role": "Super Admin", "x-user-id": "admin@sentitron.ai"}
    await client.post("/api/settings", json={"toxicity_threshold": 70}, headers=headers)

    payload = make_complaint(toxicity=91.0)
    res = await client.post("/ingestion/mock", json=payload)
    assert res.status_code == 200

    notif_res = await client.get("/api/notifications")
    tox_notifs = [n for n in notif_res.json() if n["title"] == "Toxicity Spike Detected"]
    assert len(tox_notifs) >= 1
    assert tox_notifs[0]["severity"] == "HIGH"
    assert tox_notifs[0]["related_entity_id"] == payload["complaint_id"]


@pytest.mark.asyncio
async def test_escalation_flag_triggers_warning_notification(client):
    """A complaint flagged for escalation must generate a WARNING notification."""
    payload = make_complaint(escalation="true")
    res = await client.post("/ingestion/mock", json=payload)
    assert res.status_code == 200

    notif_res = await client.get("/api/notifications")
    esc_notifs = [n for n in notif_res.json() if n["title"] == "Automated Escalation"]
    assert len(esc_notifs) >= 1
    assert esc_notifs[0]["severity"] == "WARNING"


@pytest.mark.asyncio
async def test_anonymous_critical_triggers_critical_notification(client):
    """An anonymous Critical report must fire a CRITICAL security notification."""
    payload = {"category": "Security", "description": "Suspicious person near gate", "urgency": "Critical"}
    res = await client.post("/api/incidents/anonymous", json=payload)
    assert res.status_code == 200
    incident_id = res.json()["id"]

    notif_res = await client.get("/api/notifications")
    crit = [n for n in notif_res.json() if n["severity"] == "CRITICAL" and n["related_entity_id"] == incident_id]
    assert len(crit) >= 1


@pytest.mark.asyncio
async def test_anonymous_high_triggers_high_notification(client):
    """An anonymous High report must fire a HIGH notification."""
    payload = {"category": "Harassment", "description": "Bullying in cafeteria", "urgency": "High"}
    res = await client.post("/api/incidents/anonymous", json=payload)
    assert res.status_code == 200
    incident_id = res.json()["id"]

    notif_res = await client.get("/api/notifications")
    high_notifs = [n for n in notif_res.json() if n["severity"] == "HIGH" and n["related_entity_id"] == incident_id]
    assert len(high_notifs) >= 1


@pytest.mark.asyncio
async def test_data_quality_timestamp_present(client):
    """All returned complaints must carry a non-null timestamp."""
    payload = make_complaint()
    await client.post("/ingestion/mock", json=payload)
    feed = await client.get("/api/incidents")
    for complaint in feed.json():
        assert complaint.get("timestamp") is not None, f"Missing timestamp: {complaint['complaint_id']}"


@pytest.mark.asyncio
async def test_low_toxicity_no_extra_notification(client):
    """A complaint below threshold must NOT create a Toxicity notification for that ID."""
    headers = {"x-user-role": "Super Admin", "x-user-id": "admin@sentitron.ai"}
    await client.post("/api/settings", json={"toxicity_threshold": 70}, headers=headers)

    payload = make_complaint(toxicity=30.0)
    await client.post("/ingestion/mock", json=payload)

    notif_res = await client.get("/api/notifications")
    tox_notifs = [
        n for n in notif_res.json()
        if n["title"] == "Toxicity Spike Detected" and n["related_entity_id"] == payload["complaint_id"]
    ]
    assert len(tox_notifs) == 0
