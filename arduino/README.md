# WMM — ESP32 Firmware

Original embedded firmware for the Wrist Motion Monitor hardware. Runs on an **ESP32** and reads from two **Adafruit BNO055** 9-DOF IMU sensors over I2C, then transmits sensor data to a connected client via **Bluetooth Low Energy (BLE)**.

## Hardware

| Component | Details |
|---|---|
| Microcontroller | ESP32 (Arduino framework) |
| IMU 1 | Adafruit BNO055 — I2C address `0x28` |
| IMU 2 | Adafruit BNO055 — I2C address `0x29` |
| Communication | BLE GATT (notify) |
| Sample Rate | 10ms (100Hz) |

The two IMUs are mounted at different points on the wrist/forearm to capture relative joint motion.

## Primary Sketch

**`BLE/WMM_BLE2_notify.ino`** — the production firmware. On connection it samples both IMUs at 100Hz and notifies the client with comma-delimited strings over separate BLE characteristics:

```
# Per IMU, per sample:
w,x,y,z;          — unit quaternion
sx,sy,sz;         — linear acceleration (m/s²)
gx,gy,gz;         — gyroscope (deg/s)
sys,g,a,m;        — calibration status (0–3 each)
```

Two operating modes are selectable via `device_mode`:
- **Passive (0)** — buffers 400 readings on-device, then flushes in bulk
- **Active (1)** — streams each reading immediately via BLE notify

## BLE Profile

| UUID | Characteristic |
|---|---|
| `4fafc201-...` | Service |
| `beb5483e-...` | IMU 1 — Quaternion |
| `1773bab4-...` | IMU 1 — Calibration |
| `9d0a663e-...` | IMU 1 — Linear Acceleration |
| `a94b0060-...` | IMU 1 — Gyroscope |
| `a860ec8e-...` | IMU 2 — Quaternion |
| `776f298c-...` | IMU 2 — Calibration |
| `cd356156-...` | IMU 2 — Linear Acceleration |
| `1cb3d4f1-...` | IMU 2 — Gyroscope |

## Other Sketches

| File | Purpose |
|---|---|
| `IMUQuat/IMUQuat.ino` | Standalone dual-IMU quaternion reader (Serial output, no BLE) |
| `BLE/BLE_scan_rssi.ino` | BLE device discovery utility |
| `BLE/WMM_BLE_passive.ino` | Earlier passive-only prototype |
| `flex_ext/flex_ext.ino` | Optional analog flex/extension sensor reader |

## Dependencies

Install via Arduino Library Manager:
- `Adafruit BNO055`
- `Adafruit Unified Sensor`
- `ESP32 BLE Arduino` (included with ESP32 board package)
