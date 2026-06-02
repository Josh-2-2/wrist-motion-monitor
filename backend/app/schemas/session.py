from datetime import datetime
from pydantic import BaseModel


class SessionCreate(BaseModel):
    athlete_id: int
    label: str | None = None


class SessionResponse(BaseModel):
    id: int
    athlete_id: int
    label: str | None
    recorded_at: datetime
    duration_ms: int | None

    model_config = {"from_attributes": True}
