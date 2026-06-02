from httpx import AsyncClient


async def test_create_athlete(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/athletes/",
        json={"name": "Jane Doe", "sport": "Tennis", "notes": "Serve analysis"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Jane Doe"
    assert data["sport"] == "Tennis"
    assert data["notes"] == "Serve analysis"
    assert "id" in data
    assert "created_at" in data


async def test_create_athlete_minimal(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/athletes/", json={"name": "John"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "John"
    assert data["sport"] is None
    assert data["notes"] is None


async def test_list_athletes_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/athletes/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_athletes_sorted_by_name(client: AsyncClient, auth_headers: dict):
    await client.post("/athletes/", json={"name": "Zara"}, headers=auth_headers)
    await client.post("/athletes/", json={"name": "Alice"}, headers=auth_headers)
    await client.post("/athletes/", json={"name": "Mike"}, headers=auth_headers)
    resp = await client.get("/athletes/", headers=auth_headers)
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert names == sorted(names)


async def test_get_athlete(client: AsyncClient, auth_headers: dict):
    create = await client.post("/athletes/", json={"name": "Charlie"}, headers=auth_headers)
    athlete_id = create.json()["id"]
    resp = await client.get(f"/athletes/{athlete_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Charlie"


async def test_get_athlete_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/athletes/999", headers=auth_headers)
    assert resp.status_code == 404


async def test_update_athlete_partial(client: AsyncClient, auth_headers: dict):
    create = await client.post(
        "/athletes/", json={"name": "Dave", "sport": "Baseball"}, headers=auth_headers
    )
    athlete_id = create.json()["id"]
    resp = await client.patch(
        f"/athletes/{athlete_id}", json={"sport": "Basketball"}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sport"] == "Basketball"
    assert data["name"] == "Dave"  # unchanged


async def test_update_athlete_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.patch("/athletes/999", json={"name": "Ghost"}, headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_athlete(client: AsyncClient, auth_headers: dict):
    create = await client.post("/athletes/", json={"name": "Eve"}, headers=auth_headers)
    athlete_id = create.json()["id"]
    resp = await client.delete(f"/athletes/{athlete_id}", headers=auth_headers)
    assert resp.status_code == 204
    gone = await client.get(f"/athletes/{athlete_id}", headers=auth_headers)
    assert gone.status_code == 404


async def test_delete_athlete_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.delete("/athletes/999", headers=auth_headers)
    assert resp.status_code == 404


async def test_athletes_require_auth(client: AsyncClient):
    resp = await client.get("/athletes/")
    assert resp.status_code == 401
