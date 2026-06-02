import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import AsyncSessionLocal
from app.models.imu_reading import IMUReading
from app.models.session import Session
from app.schemas.imu_reading import IMUReadingCreate
from app.services.kafka import publish_reading
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stream"])


@router.websocket("/sessions/{session_id}/stream")
async def stream_readings(session_id: int, websocket: WebSocket):
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Session).where(Session.id == session_id))
        if not result.scalar_one_or_none():
            await websocket.close(code=4004, reason="Session not found")
            return

    count = 0
    logger.info("WebSocket stream opened for session %d", session_id)

    try:
        while True:
            raw = await websocket.receive_text()
            payload = IMUReadingCreate(**json.loads(raw))

            async with AsyncSessionLocal() as db:
                reading = IMUReading(session_id=session_id, **payload.model_dump())
                db.add(reading)
                await db.commit()

            await publish_reading(session_id, payload.model_dump())
            count += 1
            await websocket.send_text(json.dumps({"ack": count}))

    except WebSocketDisconnect:
        logger.info("WebSocket stream closed for session %d — %d readings received", session_id, count)
