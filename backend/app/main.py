from contextlib import asynccontextmanager
from fastapi import FastAPI

import app.models  # noqa: F401 — registers all models with Base.metadata
from app.database import engine, Base
from app.routers import auth, athletes, sessions, stream
from app.services.kafka import stop_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await stop_producer()
    await engine.dispose()


app = FastAPI(
    title="Wrist Motion Monitor API",
    description=(
        "Backend API for capturing, storing, and streaming wrist motion data "
        "from dual BNO055 IMU sensors. Supports batch uploads and live WebSocket streaming."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(athletes.router)
app.include_router(sessions.router)
app.include_router(stream.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
