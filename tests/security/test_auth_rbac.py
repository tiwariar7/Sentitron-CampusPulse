import pytest

@pytest.mark.asyncio
async def test_user_registration_and_login(client):
    """
    Test standard user registration, duplicate username handling,
    login flow, password validation, and profile retrieval.
    """
    # 1. Register a new user
    reg_payload = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass123",
        "role": "user",
        "department": "CSE"
    }
    reg_res = await client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["username"] == "testuser"
    assert reg_data["role"] == "user"

    # 2. Register duplicate username — should fail
    duplicate_res = await client.post("/api/auth/register", json=reg_payload)
    assert duplicate_res.status_code == 400
    assert "Username already registered" in duplicate_res.json()["detail"]

    # 3. Login with invalid password
    bad_login_res = await client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert bad_login_res.status_code == 401

    # 4. Login with correct password
    login_res = await client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    token = login_data["access_token"]

    # 5. Access profile endpoint with valid token
    me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "testuser"
    assert me_data["role"] == "user"

    # 6. Access profile endpoint without token — should fail
    me_fail_res = await client.get("/api/auth/me")
    assert me_fail_res.status_code == 401


@pytest.mark.asyncio
async def test_role_based_access_control(client):
    """
    Test RBAC validation across endpoints for different roles:
    Admin, Moderator, Standard User, and Guest.
    """
    # Register moderator
    await client.post("/api/auth/register", json={
        "username": "mod_user",
        "email": "mod@example.com",
        "password": "modpass123",
        "role": "moderator"
    })
    mod_login = await client.post("/api/auth/login", json={
        "username": "mod_user",
        "password": "modpass123"
    })
    mod_token = mod_login.json()["access_token"]

    # Register standard user
    await client.post("/api/auth/register", json={
        "username": "std_user",
        "email": "std@example.com",
        "password": "stdpass123",
        "role": "user"
    })
    std_login = await client.post("/api/auth/login", json={
        "username": "std_user",
        "password": "stdpass123"
    })
    std_token = std_login.json()["access_token"]

    # Register guest user
    await client.post("/api/auth/register", json={
        "username": "guest_user",
        "email": "guest@example.com",
        "password": "guestpass123",
        "role": "guest"
    })
    guest_login = await client.post("/api/auth/login", json={
        "username": "guest_user",
        "password": "guestpass123"
    })
    guest_token = guest_login.json()["access_token"]

    # 1. Test settings endpoints
    # Admin (fallback default seed or via token/header) - we use fallback headers first
    admin_settings_get = await client.get("/api/settings", headers={"x-user-role": "Super Admin"})
    assert admin_settings_get.status_code == 200

    admin_settings_post = await client.post(
        "/api/settings",
        json={"critical_escalation_score": 88},
        headers={"x-user-role": "Super Admin"}
    )
    assert admin_settings_post.status_code == 200

    # Moderator trying to view settings - allowed (Analytics Admin/Moderator view allowed)
    mod_settings_get = await client.get("/api/settings", headers={"Authorization": f"Bearer {mod_token}"})
    assert mod_settings_get.status_code == 200

    # Moderator trying to edit settings - blocked
    mod_settings_post = await client.post(
        "/api/settings",
        json={"critical_escalation_score": 50},
        headers={"Authorization": f"Bearer {mod_token}"}
    )
    assert mod_settings_post.status_code == 403

    # Standard user trying to view settings - blocked
    std_settings_get = await client.get("/api/settings", headers={"Authorization": f"Bearer {std_token}"})
    assert std_settings_get.status_code == 403

    # 2. Test clusters endpoint
    # Moderator - allowed
    mod_clusters = await client.get("/api/clusters/active", headers={"Authorization": f"Bearer {mod_token}"})
    assert mod_clusters.status_code == 200

    # Standard User - blocked
    std_clusters = await client.get("/api/clusters/active", headers={"Authorization": f"Bearer {std_token}"})
    assert std_clusters.status_code == 403

    # Guest - blocked
    guest_clusters = await client.get("/api/clusters/active", headers={"Authorization": f"Bearer {guest_token}"})
    assert guest_clusters.status_code == 403


@pytest.mark.asyncio
async def test_fallback_compatibility_headers(client):
    """
    Assert that the backward compatibility header fallback works
    correctly for legacy integration tests.  Uses unique x-user-id
    values so each sub-test creates an isolated mock user.
    """
    # 1. Super Admin header → should reach settings (200)
    res_admin = await client.get(
        "/api/settings",
        headers={
            "x-user-role": "Super Admin",
            "x-user-id": "fallback_admin@sentitron.ai",
        },
    )
    assert res_admin.status_code == 200

    # 2. Department Admin header → settings write must be blocked (403)
    #    Uses a different x-user-id so it gets its own fresh mock user
    #    with role=moderator and cannot write settings.
    res_dept = await client.post(
        "/api/settings",
        json={"critical_escalation_score": 50},
        headers={
            "x-user-role": "Department Admin",
            "x-user-id": "fallback_dept@sentitron.ai",
        },
    )
    assert res_dept.status_code == 403

