from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.athlete import Athlete
from app.models.session import Session
from app.models.imu_reading import IMUReading
from app.models.user import User
from app.schemas.session import SessionCreate, SessionResponse
from app.schemas.imu_reading import IMUBatchUpload, IMUReadingResponse
from app.services.kafka import publish_reading

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Athlete).where(Athlete.id == payload.athlete_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Athlete not found")

    session = Session(**payload.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Session).order_by(Session.recorded_at.desc()))
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/upload", response_model=dict)
async def upload_readings(
    session_id: int,
    payload: IMUBatchUpload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    readings = [
        IMUReading(session_id=session_id, **r.model_dump()) for r in payload.readings
    ]
    db.add_all(readings)

    if payload.readings:
        session.duration_ms = (
            payload.readings[-1].timestamp_ms - payload.readings[0].timestamp_ms
        )

    await db.commit()

    for r in payload.readings:
        await publish_reading(session_id, r.model_dump())

    return {"uploaded": len(readings)}


@router.get("/{session_id}/readings", response_model=list[IMUReadingResponse])
async def get_readings(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(IMUReading)
        .where(IMUReading.session_id == session_id)
        .order_by(IMUReading.timestamp_ms)
    )
    return result.scalars().all()
