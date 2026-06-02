from datetime import datetime
from pydantic import BaseModel


class AthleteCreate(BaseModel):
    name: str
    sport: str | None = None
    notes: str | None = None


class AthleteUpdate(BaseModel):
    name: str | None = None
    sport: str | None = None
    notes: str | None = None


class AthleteResponse(BaseModel):
    id: int
    name: str
    sport: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
