from sqlalchemy import Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class IMUReading(Base):
    __tablename__ = "imu_readings"
    __table_args__ = (
        # Composite index for fast time-ordered queries within a session
        Index("ix_imu_readings_session_timestamp", "session_id", "timestamp_ms"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Quaternion components (unit quaternion representing wrist orientation)
    q0: Mapped[float] = mapped_column(Float, nullable=False)
    q1: Mapped[float] = mapped_column(Float, nullable=False)
    q2: Mapped[float] = mapped_column(Float, nullable=False)
    q3: Mapped[float] = mapped_column(Float, nullable=False)

    # Linear acceleration (m/s²)
    accel_x: Mapped[float | None] = mapped_column(Float)
    accel_y: Mapped[float | None] = mapped_column(Float)
    accel_z: Mapped[float | None] = mapped_column(Float)

    # Gyroscope (deg/s)
    gyro_x: Mapped[float | None] = mapped_column(Float)
    gyro_y: Mapped[float | None] = mapped_column(Float)
    gyro_z: Mapped[float | None] = mapped_column(Float)

    session: Mapped["Session"] = relationship("Session", back_populates="readings")
