import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from appify_connector.main import create_app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    app = create_app()
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
            yield c


async def test_login_list_describe_logout(client: AsyncClient, appify_creds: dict) -> None:
    resp = await client.post("/api/v1/auth/login", json=appify_creds)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    token = body["access_token"]
    assert body["instance_url"].startswith("https://")

    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/objects", headers=headers)
    assert resp.status_code == 200
    objects = resp.json()
    assert len(objects) > 0
    assert {"name", "label", "sor", "flex_name", "id"} <= set(objects[0])

    target = objects[0]["name"]
    resp = await client.get(f"/api/v1/objects/{target}", headers=headers)
    assert resp.status_code == 200
    desc = resp.json()
    assert desc["name"] == target
    assert isinstance(desc["fields"], list)
    assert len(desc["fields"]) > 0

    resp = await client.get("/api/v1/sors", headers=headers)
    assert resp.status_code == 200
    sors = resp.json()
    assert any(s.get("short_name") for s in sors)

    resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert resp.status_code == 204

    resp = await client.get("/api/v1/objects", headers=headers)
    assert resp.status_code == 401


async def test_unknown_object_returns_404(client: AsyncClient, appify_creds: dict) -> None:
    resp = await client.post("/api/v1/auth/login", json=appify_creds)
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/objects/this_object_does_not_exist_xyz",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "OBJECT_NOT_FOUND"


async def test_missing_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/objects")
    assert resp.status_code == 401


async def test_invalid_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/objects", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401
