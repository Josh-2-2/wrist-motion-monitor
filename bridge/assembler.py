import asyncio
import time


def _parse(data: bytearray) -> list[float]:
    return [float(v) for v in data.decode().rstrip(";").split(",")]


class ReadingAssembler:
    """
    Buffers BLE notify callbacks from three separate characteristics
    (quaternion, linear acceleration, gyroscope) and emits a complete
    IMU reading to a shared queue once all fields arrive for one sample.

    Two assembler instances share a single queue so readings from both
    IMUs are interleaved in arrival order and forwarded together.
    """

    _REQUIRED = frozenset([
        "q0", "q1", "q2", "q3",
        "accel_x", "accel_y", "accel_z",
        "gyro_x", "gyro_y", "gyro_z",
    ])

    def __init__(self, imu_id: int, queue: asyncio.Queue):
        self.imu_id = imu_id
        self._queue = queue
        self._buf: dict = {}
        self._start_ms = int(time.time() * 1000)

    # ── BLE notify callbacks ──────────────────────────────────────────────────

    def on_quat(self, _sender, data: bytearray):
        w, x, y, z = _parse(data)
        self._buf.update({"q0": w, "q1": x, "q2": y, "q3": z})
        self._try_emit()

    def on_accel(self, _sender, data: bytearray):
        x, y, z = _parse(data)
        self._buf.update({"accel_x": x, "accel_y": y, "accel_z": z})
        self._try_emit()

    def on_gyro(self, _sender, data: bytearray):
        x, y, z = _parse(data)
        self._buf.update({"gyro_x": x, "gyro_y": y, "gyro_z": z})
        self._try_emit()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _try_emit(self):
        if self._REQUIRED <= self._buf.keys():
            self._queue.put_nowait({
                "imu_id": self.imu_id,
                "timestamp_ms": int(time.time() * 1000) - self._start_ms,
                **self._buf,
            })
            self._buf = {}
