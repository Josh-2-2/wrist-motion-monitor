import pytest
from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    resp = await client.post("/auth/register", json={"email": "new@wmm.dev", "password": "pass123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@wmm.dev"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@wmm.dev", "password": "pass123"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


async def test_login_success(client: AsyncClient):
    await client.post("/auth/register", json={"email": "login@wmm.dev", "password": "pass123"})
    resp = await client.post("/auth/login", data={"username": "login@wmm.dev", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json={"email": "wp@wmm.dev", "password": "pass123"})
    resp = await client.post("/auth/login", data={"username": "wp@wmm.dev", "password": "wrongpass"})
    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post("/auth/login", data={"username": "ghost@wmm.dev", "password": "pass123"})
    assert resp.status_code == 401


async def test_protected_route_without_token(client: AsyncClient):
    resp = await client.get("/athletes/")
    assert resp.status_code == 401


async def test_protected_route_with_invalid_token(client: AsyncClient):
    resp = await client.get("/athletes/", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401
