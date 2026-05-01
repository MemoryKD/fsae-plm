import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/auth/register", json={
        "username": "testuser",
        "password": "testpass123",
        "role": "designer",
        "team": "悬架组"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["role"] == "designer"
    assert "id" in data


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/auth/register", json={
        "username": "loginuser",
        "password": "testpass123",
        "role": "designer"
    })
    resp = await client.post("/api/auth/login", json={
        "username": "loginuser",
        "password": "testpass123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "username": "wrongpass",
        "password": "correct",
        "role": "designer"
    })
    resp = await client.post("/api/auth/login", json={
        "username": "wrongpass",
        "password": "wrong"
    })
    assert resp.status_code == 401
