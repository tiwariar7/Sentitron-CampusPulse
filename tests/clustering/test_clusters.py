"""
Semantic Clustering verification.
Section 5 — Cluster grouping correctness, duplicate detection, cluster-triggered alerts.
"""
import pytest
import uuid


def hostel_wifi_complaint(cluster_id: str):
    variants = [
        "WiFi in hostel is completely down.",
        "Hostel internet disconnected again for second day.",
        "Unable to access internet from my hostel room.",
        "No internet connection in block B hostel.",
        "Hostel wifi stopped working since morning.",
        "WiFi router in hostel block is unresponsive.",
    ]
    return [
        {
            "complaint_id": f"CLU-{uuid.uuid4().hex[:6].upper()}",
            "source": "TestSuite",
            "department": "IT",
            "category": "Infrastructure",
            "subcategory": "Network",
            "complaint_text": text,
            "sentiment_score": -0.6,
            "urgency_level": 3,
            "escalation_flag": "false",
            "resolved": "false",
            "duplicate_group_id": cluster_id,
            "toxicity_score": 5.0,
            "anonymous": "false",
            "response_delay_hours": "0",
        }
        for text in variants
    ]


@pytest.mark.asyncio
async def test_cluster_groups_correctly(client):
    """Complaints sharing a duplicate_group_id must appear together in /api/clusters/active."""
    cluster_id = f"CLU-WIFI-{uuid.uuid4().hex[:4].upper()}"
    complaints = hostel_wifi_complaint(cluster_id)
    for c in complaints:
        await client.post("/ingestion/mock", json=c)

    res = await client.get("/api/clusters/active")
    assert res.status_code == 200
    cluster_ids = [cl["cluster_id"] for cl in res.json()]
    assert cluster_id in cluster_ids


@pytest.mark.asyncio
async def test_cluster_count_reflects_ingested_complaints(client):
    """Cluster incident_count must match the number of complaints ingested."""
    cluster_id = f"CLU-COUNT-{uuid.uuid4().hex[:4].upper()}"
    complaints = hostel_wifi_complaint(cluster_id)
    for c in complaints:
        await client.post("/ingestion/mock", json=c)

    res = await client.get("/api/clusters/active")
    matching = [cl for cl in res.json() if cl["cluster_id"] == cluster_id]
    assert len(matching) == 1
    assert matching[0]["incident_count"] == len(complaints)


@pytest.mark.asyncio
async def test_rapid_cluster_growth_triggers_notification(client):
    """A cluster with 5+ incidents must trigger a HIGH cluster growth notification."""
    cluster_id = f"CLU-RAPID-{uuid.uuid4().hex[:4].upper()}"
    complaints = hostel_wifi_complaint(cluster_id)  # 6 complaints
    for c in complaints:
        await client.post("/ingestion/mock", json=c)

    # Fetch clusters — this call also evaluates growth triggers
    await client.get("/api/clusters/active")

    notif_res = await client.get("/api/notifications")
    growth_notifs = [
        n for n in notif_res.json()
        if n["title"] == "Rapid Cluster Growth Detected" and cluster_id in n["message"]
    ]
    assert len(growth_notifs) >= 1
    assert growth_notifs[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_distinct_clusters_do_not_merge(client):
    """Two complaint groups with different cluster IDs must not be merged."""
    cluster_a = f"CLU-A-{uuid.uuid4().hex[:4].upper()}"
    cluster_b = f"CLU-B-{uuid.uuid4().hex[:4].upper()}"

    for cluster_id in [cluster_a, cluster_b]:
        for c in hostel_wifi_complaint(cluster_id)[:2]:
            await client.post("/ingestion/mock", json=c)

    res = await client.get("/api/clusters/active")
    cluster_ids = [cl["cluster_id"] for cl in res.json()]
    assert cluster_a in cluster_ids
    assert cluster_b in cluster_ids
