from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sport: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="athlete", cascade="all, delete-orphan"
    )
