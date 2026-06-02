# WMM — BLE Bridge

Connects to the ESP32 as a BLE GATT client and streams IMU readings to the FastAPI backend in real time over WebSocket.

## How it works

```
ESP32 (BLE notify) ──► assembler.py ──► WebSocket ──► FastAPI /sessions/{id}/stream
```

The bridge subscribes to six BLE characteristics (quaternion, linear acceleration, gyroscope × 2 IMUs). Since each characteristic notifies independently, `ReadingAssembler` buffers partial updates per IMU and emits a complete reading only once all three fields have arrived for the same sample.

## Setup

```bash
cd bridge
pip install -r requirements.txt
```

Requires a BLE-capable machine (laptop or Raspberry Pi). On Linux you may need to run with `sudo` or grant BLE permissions to your user.

## Usage

First create a session via the API (or Swagger UI), then run the bridge with that session ID:

```bash
python main.py --session-id 1 --api-url http://localhost:8000
```

The bridge will:
1. Scan for a BLE device named `WMM`
2. Connect and subscribe to all IMU characteristics
3. Open a WebSocket to the API and stream readings
4. Log progress every 100 readings
5. Automatically reconnect (with exponential backoff) on BLE or WebSocket failure

## Options

| Flag | Default | Description |
|---|---|---|
| `--session-id` | required | API session ID to stream into |
| `--api-url` | `http://localhost:8000` | FastAPI base URL |
| `--device` | `WMM` | BLE device name to scan for |
