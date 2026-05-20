import pytest


@pytest.mark.asyncio
async def test_refresh_token_lifecycle(client):
    # 1. Register a fresh test user
    reg_res = await client.post("/api/auth/register", json={
        "username": "refresh_user",
        "email": "refresh_user@example.com",
        "password": "refresh_password_123",
        "role": "user"
    })
    assert reg_res.status_code == 200

    # 2. Login -> should get both access and refresh tokens
    login_res = await client.post("/api/auth/login", json={
        "username": "refresh_user",
        "password": "refresh_password_123"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 3. Use refresh token to get a new access token
    refresh_res = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    new_access_token = new_tokens["access_token"]
    new_refresh_token = new_tokens["refresh_token"]

    # 4. Logout (revokes refresh token)
    logout_res = await client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert logout_res.status_code == 200

    # 5. Trying to refresh with the revoked or old refresh token should fail
    fail_refresh = await client.post("/api/auth/refresh", json={
        "refresh_token": new_refresh_token
    })
    assert fail_refresh.status_code == 401
