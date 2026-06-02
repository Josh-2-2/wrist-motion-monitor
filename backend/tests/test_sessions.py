import pytest
from httpx import AsyncClient

SAMPLE_READINGS = [
    {"timestamp_ms": 0,  "q0": 1.000, "q1": 0.000, "q2": 0.000, "q3": 0.000,
     "accel_x": 0.01, "accel_y": -0.02, "accel_z": 9.81},
    {"timestamp_ms": 10, "q0": 0.999, "q1": 0.012, "q2": 0.005, "q3": 0.001,
     "accel_x": 0.15, "accel_y": -0.10, "accel_z": 9.79},
    {"timestamp_ms": 20, "q0": 0.997, "q1": 0.045, "q2": 0.018, "q3": 0.003,
     "accel_x": 0.52, "accel_y": -0.38, "accel_z": 9.72},
]


async def _make_session(client: AsyncClient, auth_headers: dict, label: str | None = None) -> dict:
    athlete = await client.post("/athletes/", json={"name": "Test Athlete"}, headers=auth_headers)
    payload = {"athlete_id": athlete.json()["id"]}
    if label:
        payload["label"] = label
    resp = await client.post("/sessions/", json=payload, headers=auth_headers)
    return resp.json()


async def test_create_session(client: AsyncClient, auth_headers: dict):
    session = await _make_session(client, auth_headers, label="Warmup")
    assert session["label"] == "Warmup"
    assert session["duration_ms"] is None
    assert "id" in session
    assert "recorded_at" in session


async def test_create_session_without_label(client: AsyncClient, auth_headers: dict):
    session = await _make_session(client, auth_headers)
    assert session["label"] is None


async def test_create_session_invalid_athlete(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/sessions/", json={"athlete_id": 999}, headers=auth_headers)
    assert resp.status_code == 404


async def test_list_sessions(client: AsyncClient, auth_headers: dict):
    await _make_session(client, auth_headers, label="Session A")
    await _make_session(client, auth_headers, label="Session B")
    resp = await client.get("/sessions/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_sessions_ordered_by_newest(client: AsyncClient, auth_headers: dict):
    await _make_session(client, auth_headers, label="First")
    await _make_session(client, auth_headers, label="Second")
    resp = await client.get("/sessions/", headers=auth_headers)
    sessions = resp.json()
    assert sessions[0]["label"] == "Second"


async def test_get_session(client: AsyncClient, auth_headers: dict):
    created = await _make_session(client, auth_headers, label="Get Me")
    resp = await client.get(f"/sessions/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["label"] == "Get Me"


async def test_get_session_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/sessions/999", headers=auth_headers)
    assert resp.status_code == 404


async def test_upload_readings(client: AsyncClient, auth_headers: dict):
    session = await _make_session(client, auth_headers)
    resp = await client.post(
        f"/sessions/{session['id']}/upload",
        json={"readings": SAMPLE_READINGS},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["uploaded"] == 3


async def test_upload_calculates_duration(client: AsyncClient, auth_headers: dict):
    session = await _make_session(client, auth_headers)
    session_id = session["id"]
    await client.post(
        f"/sessions/{session_id}/upload",
        json={"readings": SAMPLE_READINGS},
        headers=auth_headers,
    )
    resp = await client.get(f"/sessions/{session_id}", headers=auth_headers)
    assert resp.json()["duration_ms"] == 20  # last(20) - first(0)


async def test_upload_to_missing_session(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/sessions/999/upload",
        json={"readings": SAMPLE_READINGS},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_get_readings_returns_all(client: AsyncClient, auth_headers: dict):
    session = await _make_session(client, auth_headers)
    session_id = session["id"]
    await client.post(
        f"/sessions/{session_id}/upload",
        json={"readings": SAMPLE_READINGS},
        headers=auth_headers,
    )
    resp = await client.get(f"/sessions/{session_id}/readings", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


async def test_get_readings_ordered_by_timestamp(client: AsyncClient, auth_headers: dict):
    session = await _make_session(client, auth_headers)
    session_id = session["id"]
    await client.post(
        f"/sessions/{session_id}/upload",
        json={"readings": SAMPLE_READINGS},
        headers=auth_headers,
    )
    resp = await client.get(f"/sessions/{session_id}/readings", headers=auth_headers)
    timestamps = [r["timestamp_ms"] for r in resp.json()]
    assert timestamps == sorted(timestamps)


async def test_readings_contain_quaternion_fields(client: AsyncClient, auth_headers: dict):
    session = await _make_session(client, auth_headers)
    await client.post(
        f"/sessions/{session['id']}/upload",
        json={"readings": SAMPLE_READINGS},
        headers=auth_headers,
    )
    resp = await client.get(f"/sessions/{session['id']}/readings", headers=auth_headers)
    reading = resp.json()[0]
    for field in ("q0", "q1", "q2", "q3", "accel_x", "accel_y", "accel_z"):
        assert field in reading


async def test_sessions_require_auth(client: AsyncClient):
    resp = await client.get("/sessions/")
    assert resp.status_code == 401
