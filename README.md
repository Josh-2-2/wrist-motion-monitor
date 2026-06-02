# Wrist Motion Monitor — API

![CI](https://github.com/Josh-2-2/wrist-motion-monitor/actions/workflows/ci.yml/badge.svg)

A backend API for capturing, storing, and streaming wrist motion data from dual BNO055 IMU sensors worn during athletic activity. Originally built as a senior design project at Mississippi State University, this version is a full backend rewrite using modern Python tooling.

## Architecture

```
ESP32 (BLE notify)
       │
  bleak bridge          ← bridge/main.py
  (Python, async)
       │ WebSocket
       ▼
  FastAPI Backend ──► PostgreSQL
       │
  Kafka Producer
       │
  imu.readings topic
```

The system has three components:
- **ESP32 firmware** (`arduino/`) — reads dual BNO055 IMUs at 100Hz and advertises data via BLE GATT notify
- **BLE bridge** (`bridge/`) — Python process that connects to the ESP32 as a GATT client and forwards readings to the API over WebSocket
- **FastAPI backend** (`backend/`) — receives, stores, and serves session data; also accepts batch uploads for offline recordings

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | [PostgreSQL 16](https://www.postgresql.org/) via async [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) |
| Message Streaming | [Apache Kafka](https://kafka.apache.org/) via [aiokafka](https://github.com/aio-libs/aiokafka) |
| Authentication | JWT ([python-jose](https://github.com/mpdavis/python-jose)) + bcrypt ([passlib](https://passlib.readthedocs.io/)) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/latest/) |
| Package Installer | [uv](https://github.com/astral-sh/uv) |
| Containerization | Docker + Docker Compose |
| Testing | pytest + pytest-asyncio + httpx + SQLite (in-memory) |

## Quick Start

**Prerequisites:** Docker and Docker Compose

```bash
git clone https://github.com/Josh-2-2/wrist-motion-monitor.git
cd wrist-motion-monitor/backend
cp .env.example .env        # add your own SECRET_KEY
docker compose up --build
```

The API will be available at `http://localhost:8000`.  
Interactive API docs (Swagger UI): `http://localhost:8000/docs`

## Running Tests

Tests use an in-memory SQLite database — no running services required.

```bash
docker compose run --rm api python -m pytest tests/ -v
```

**32 tests** covering auth, athlete CRUD, session management, batch upload, duration calculation, and WebSocket ingestion.

## API Reference

[**View full interactive API spec →**](https://editor.swagger.io/?url=https://raw.githubusercontent.com/Josh-2-2/wrist-motion-monitor/main/backend/openapi.json)

The spec is generated directly from the FastAPI app and committed to the repo at [`backend/openapi.json`](backend/openapi.json).

## Data Model

Each IMU reading captures the full output of a BNO055 sensor at a given timestamp:

```
imu_readings
├── session_id       FK → sessions
├── timestamp_ms     milliseconds since session start
├── q0, q1, q2, q3  unit quaternion (wrist orientation)
├── accel_x/y/z      linear acceleration (m/s²)
└── gyro_x/y/z       angular velocity (deg/s)
```

A composite index on `(session_id, timestamp_ms)` enables fast time-ordered queries across large datasets.

## Project Structure

```
backend/
├── app/
│   ├── main.py            # App entry point, lifespan, router registration
│   ├── config.py          # Settings via pydantic-settings
│   ├── database.py        # Async SQLAlchemy engine
│   ├── dependencies.py    # Shared dependencies (get_db, get_current_user)
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routers/           # Route handlers (auth, athletes, sessions, stream)
│   └── services/          # JWT auth logic, Kafka producer
├── tests/
│   ├── conftest.py        # Fixtures (test DB, client, auth headers)
│   ├── test_auth.py
│   ├── test_athletes.py
│   └── test_sessions.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Hardware

The `arduino/` directory contains the original ESP32 firmware for reading dual BNO055 IMUs over I2C and transmitting quaternion + accelerometer + gyroscope data via BLE. See [`arduino/`](arduino/) for sketches.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `SECRET_KEY` | JWT signing secret (keep private) | — |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL | `30` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address | `kafka:29092` |
| `KAFKA_TOPIC_IMU` | Topic for IMU readings | `imu.readings` |

> Kafka is **optional** — if unavailable the API logs a warning and continues operating normally without publishing.
