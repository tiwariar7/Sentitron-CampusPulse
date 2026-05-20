"""
Governance & RBAC verification.
Section 13 — Settings persistence, RBAC enforcement, audit logging.
"""
import pytest


@pytest.mark.asyncio
async def test_unauthorized_role_blocked(client):
    """Monitoring Viewer cannot write settings — 403 expected."""
    response = await client.post(
        "/api/settings",
        json={"toxicity_threshold": 50},
        headers={"x-user-role": "Monitoring Viewer", "x-user-id": "viewer@test.com"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unknown_role_blocked(client):
    """Completely unknown role is rejected."""
    response = await client.get("/api/settings", headers={"x-user-role": "Hacker"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_super_admin_can_write_settings(client):
    """Super Admin can update settings successfully."""
    response = await client.post(
        "/api/settings",
        json={"toxicity_threshold": 65},
        headers={"x-user-role": "Super Admin", "x-user-id": "admin@sentitron.ai"},
    )
    assert response.status_code == 200
    assert "toxicity_threshold" in response.json()["modified_keys"]


@pytest.mark.asyncio
async def test_settings_persisted_correctly(client):
    """Written settings must be readable back."""
    headers = {"x-user-role": "Super Admin", "x-user-id": "admin@sentitron.ai"}
    await client.post("/api/settings", json={"escalation_score_limit": 80}, headers=headers)
    get_res = await client.get("/api/settings", headers=headers)
    assert get_res.status_code == 200
    settings = get_res.json()["settings"]
    assert settings["escalation_score_limit"] == 80


@pytest.mark.asyncio
async def test_audit_log_captures_change(client):
    """Changing settings must produce an audit log entry."""
    headers = {"x-user-role": "Super Admin", "x-user-id": "auditor@sentitron.ai"}
    await client.post("/api/settings", json={"cluster_threshold": 0.78}, headers=headers)

    get_res = await client.get("/api/settings", headers=headers)
    audit_logs = get_res.json()["audit_logs"]
    assert len(audit_logs) >= 1
    # Find the log entry written by our specific admin identity
    matching = [l for l in audit_logs if l["administrator_identity"] == "auditor@sentitron.ai"]
    assert len(matching) >= 1
    assert matching[0]["action"] == "UPDATE_SETTINGS"


@pytest.mark.asyncio
async def test_monitoring_viewer_can_read(client):
    """Monitoring Viewer can GET settings but not write."""
    response = await client.get("/api/settings", headers={"x-user-role": "Monitoring Viewer"})
    assert response.status_code == 200
    # Monitoring Viewer should NOT see audit logs
    assert response.json()["audit_logs"] == []
