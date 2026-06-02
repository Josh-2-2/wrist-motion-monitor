from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), nullable=False)
    label: Mapped[str | None] = mapped_column(String)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="sessions")
    readings: Mapped[list["IMUReading"]] = relationship(
        "IMUReading", back_populates="session", cascade="all, delete-orphan"
    )
