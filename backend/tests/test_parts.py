import pytest


async def setup_auth(client):
    await client.post("/api/auth/register", json={
        "username": "partuser", "password": "pass123", "role": "designer"
    })
    resp = await client.post("/api/auth/login", json={
        "username": "partuser", "password": "pass123"
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_create_part(client):
    headers = await setup_auth(client)
    resp = await client.post("/api/parts", json={
        "part_number": "FS-SUS-001", "name": "前下摆臂", "type": "part", "subsystem": "悬架"
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["part_number"] == "FS-SUS-001"
    assert data["workflow_state"] == "设计中"


@pytest.mark.asyncio
async def test_list_parts(client):
    headers = await setup_auth(client)
    await client.post("/api/parts", json={
        "part_number": "FS-SUS-001", "name": "前下摆臂", "type": "part"
    }, headers=headers)
    resp = await client.get("/api/parts", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_search_parts(client):
    headers = await setup_auth(client)
    await client.post("/api/parts", json={
        "part_number": "FS-SUS-001", "name": "前下摆臂", "type": "part"
    }, headers=headers)
    resp = await client.get("/api/parts?search=摆臂", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
