from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.models.athlete import Athlete
from app.models.user import User
from app.schemas.athlete import AthleteCreate, AthleteUpdate, AthleteResponse

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.post("/", response_model=AthleteResponse, status_code=status.HTTP_201_CREATED)
async def create_athlete(
    payload: AthleteCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    athlete = Athlete(**payload.model_dump())
    db.add(athlete)
    await db.commit()
    await db.refresh(athlete)
    return athlete


@router.get("/", response_model=list[AthleteResponse])
async def list_athletes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Athlete).order_by(Athlete.name))
    return result.scalars().all()


@router.get("/{athlete_id}", response_model=AthleteResponse)
async def get_athlete(
    athlete_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete


@router.patch("/{athlete_id}", response_model=AthleteResponse)
async def update_athlete(
    athlete_id: int,
    payload: AthleteUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(athlete, field, value)

    await db.commit()
    await db.refresh(athlete)
    return athlete


@router.delete("/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_athlete(
    athlete_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    await db.delete(athlete)
    await db.commit()
