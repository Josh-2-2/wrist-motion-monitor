from pydantic import BaseModel


class IMUReadingCreate(BaseModel):
    timestamp_ms: int
    q0: float
    q1: float
    q2: float
    q3: float
    accel_x: float | None = None
    accel_y: float | None = None
    accel_z: float | None = None
    gyro_x: float | None = None
    gyro_y: float | None = None
    gyro_z: float | None = None


class IMUBatchUpload(BaseModel):
    readings: list[IMUReadingCreate]


class IMUReadingResponse(BaseModel):
    id: int
    session_id: int
    timestamp_ms: int
    q0: float
    q1: float
    q2: float
    q3: float
    accel_x: float | None
    accel_y: float | None
    accel_z: float | None
    gyro_x: float | None
    gyro_y: float | None
    gyro_z: float | None

    model_config = {"from_attributes": True}
