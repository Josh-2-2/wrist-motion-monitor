# Wrist Motion Monitor — API

A backend API for capturing, storing, and streaming wrist motion data from dual BNO055 IMU sensors worn during athletic activity. Originally built as a senior design project at Mississippi State University, this version is a full backend rewrite using modern Python tooling.

## Architecture

```
ESP32 (BLE) ──► Client / Test ──► FastAPI Backend ──► PostgreSQL
                                          │
                                     Kafka Producer
                                          │
                                   imu.readings topic
```

The API supports two ingestion modes:
- **Batch upload** — a completed session's readings are uploaded as a JSON payload after recording
- **Live stream** — a WebSocket connection streams individual readings in real time as they arrive from the sensor

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

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create a new user account |
| `POST` | `/auth/login` | Obtain a JWT access token |

### Athletes
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/athletes/` | Create an athlete profile |
| `GET` | `/athletes/` | List all athletes |
| `GET` | `/athletes/{id}` | Get a specific athlete |
| `PATCH` | `/athletes/{id}` | Update athlete details |
| `DELETE` | `/athletes/{id}` | Delete an athlete |

### Sessions & IMU Data
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sessions/` | Create a new recording session |
| `GET` | `/sessions/` | List all sessions |
| `GET` | `/sessions/{id}` | Get session details |
| `POST` | `/sessions/{id}/upload` | Batch upload IMU readings |
| `GET` | `/sessions/{id}/readings` | Retrieve all readings for a session |
| `WS` | `/sessions/{id}/stream` | Live-stream readings via WebSocket |

### Health
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |

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
