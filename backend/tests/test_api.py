import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture()
async def client(override_get_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_create_user(client: AsyncClient):
    resp = await client.post("/api/users", json={"name": "alice", "email": "alice@email.com", "password": "password"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "alice"

    # dupe should fail
    resp2 = await client.post("/api/users", json={"name": "alice2", "email": "alice@email.com", "password": "password"})
    assert resp2.status_code == 400


async def test_groups_and_messages(client: AsyncClient):
    resp = await client.post("/api/groups", json={"name": "General"})
    assert resp.status_code == 201
    group = resp.json()

    u = (await client.post("/api/users", json={"name": "testguy", "email": "testguy@email.com", "password": "password"})).json()
    await client.post(f"/api/groups/{group['id']}/members/{u['id']}")

    msgs = await client.get(f"/api/groups/{group['id']}/messages")
    assert msgs.json() == []


async def test_ws_chat(override_get_db):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        u = (await client.post("/api/users", json={"name": "dave", "email": "dave@email.com", "password": "password"})).json()
        group = (await client.post("/api/groups", json={"name": "test room"})).json()
        await client.post(f"/api/groups/{group['id']}/members/{u['id']}")

    from starlette.testclient import TestClient
    with TestClient(app) as tc:
        with tc.websocket_connect(f"/ws/{group['id']}/{u['id']}") as ws:
            presence = ws.receive_json()
            assert presence["type"] == "presence"

            ws.send_json({"content": "Hello!"})
            msg = ws.receive_json()
            assert msg["content"] == "Hello!"
            assert msg["sender_name"] == "dave"
