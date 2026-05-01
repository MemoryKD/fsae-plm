import pytest


async def get_admin_token(client):
    await client.post("/api/auth/register", json={
        "username": "admin", "password": "admin123", "role": "admin"
    })
    resp = await client.post("/api/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_list_users(client):
    token = await get_admin_token(client)
    resp = await client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_update_user_role(client):
    token = await get_admin_token(client)
    resp = await client.post("/api/auth/register", json={
        "username": "designer1", "password": "pass123", "role": "designer"
    })
    user_id = resp.json()["id"]
    resp = await client.put(
        f"/api/users/{user_id}/role",
        json={"role": "manager"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "manager"
