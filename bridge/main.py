"""
WMM BLE → WebSocket Bridge
───────────────────────────
Connects to the ESP32 as a BLE GATT client, subscribes to quaternion,
linear acceleration, and gyroscope notify characteristics for both IMUs,
assembles complete readings, and streams them to the FastAPI WebSocket
endpoint in real time.

Usage:
    python main.py --session-id 1 --api-url http://localhost:8000
"""

import argparse
import asyncio
import json
import logging

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
import websockets
from websockets.exceptions import WebSocketException

from assembler import ReadingAssembler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("wmm-bridge")

DEVICE_NAME = "WMM"

# UUIDs from WMM_BLE2_notify.ino
CHARS = {
    "imu1_quat":   "beb5483e-36e1-4688-b7f5-ea07361b26a8",
    "imu1_linear": "9d0a663e-35a2-4649-a4e6-abb3dd5fcf59",
    "imu1_gyro":   "a94b0060-62dc-4f06-9f52-be1dfa5b36f5",
    "imu2_quat":   "a860ec8e-b2f8-48ec-9ecf-9d20c7b50738",
    "imu2_linear": "cd356156-f015-4c8a-bc03-d081e2cfeb39",
    "imu2_gyro":   "1cb3d4f1-5adc-4f44-8cd6-382673b2473e",
}


def _ws_url(api_url: str, session_id: int) -> str:
    base = api_url.replace("http://", "ws://").replace("https://", "wss://")
    return f"{base}/sessions/{session_id}/stream"


async def _scan(name: str):
    log.info("Scanning for '%s'...", name)
    device = await BleakScanner.find_device_by_name(name, timeout=15.0)
    if not device:
        raise RuntimeError(f"'{name}' not found — is the ESP32 powered on?")
    log.info("Found  %s  [%s]", device.name, device.address)
    return device


async def run(session_id: int, api_url: str, device_name: str):
    url = _ws_url(api_url, session_id)
    device = await _scan(device_name)

    queue: asyncio.Queue = asyncio.Queue()
    imu1 = ReadingAssembler(imu_id=1, queue=queue)
    imu2 = ReadingAssembler(imu_id=2, queue=queue)

    async with BleakClient(device) as ble:
        log.info("BLE connected")

        await ble.start_notify(CHARS["imu1_quat"],   imu1.on_quat)
        await ble.start_notify(CHARS["imu1_linear"], imu1.on_accel)
        await ble.start_notify(CHARS["imu1_gyro"],   imu1.on_gyro)
        await ble.start_notify(CHARS["imu2_quat"],   imu2.on_quat)
        await ble.start_notify(CHARS["imu2_linear"], imu2.on_accel)
        await ble.start_notify(CHARS["imu2_gyro"],   imu2.on_gyro)

        log.info("Subscribed to all IMU characteristics — streaming to %s", url)

        async with websockets.connect(url) as ws:
            sent = 0
            while ble.is_connected:
                reading = await asyncio.wait_for(queue.get(), timeout=5.0)

                # Strip imu_id before sending — the API schema doesn't include it
                payload = {k: v for k, v in reading.items() if k != "imu_id"}
                await ws.send(json.dumps(payload))
                ack = json.loads(await ws.recv())

                sent += 1
                if sent % 100 == 0:
                    log.info(
                        "IMU%d  streamed %d readings  (server ack: %s)",
                        reading["imu_id"], sent, ack,
                    )


async def main():
    parser = argparse.ArgumentParser(description="WMM BLE → WebSocket bridge")
    parser.add_argument("--session-id", type=int, required=True, help="API session ID to stream into")
    parser.add_argument("--api-url",    default="http://localhost:8000",  help="FastAPI base URL")
    parser.add_argument("--device",     default=DEVICE_NAME,              help="BLE device name")
    args = parser.parse_args()

    backoff = 1
    while True:
        try:
            await run(args.session_id, args.api_url, args.device)
            backoff = 1
        except (BleakError, WebSocketException, RuntimeError, asyncio.TimeoutError) as e:
            log.error("%s — retrying in %ds", e, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    asyncio.run(main())
