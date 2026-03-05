# WiFi Store-and-Forward Batch Upload System

## Overview

Replaces LTE cellular connectivity with WiFi for battery data upload. Data always accumulates on the SD card. When WiFi is available, unsent historical entries are batched and uploaded alongside the current live reading.

## Architecture

```
[Sensor read + getData()]
    |
    v
[logDataToSdCard()] --> appends line to /sd/data.csv
    |
    v
[logDataToInternetWifi()]
    |
    +-- connectWifi() --> fail? set error flag, return (data safe on SD)
    |
    +-- Authenticate (POST /auth/battery-login)
    |
    +-- Send current reading (POST /webhook/live-data)
    |
    +-- sendHistoricalBatches():
    |       Read FRAM pointer -> open CSV -> skip sent lines
    |       Loop: read 50 lines -> POST /webhook/batch-live-data
    |         on success: advance FRAM pointer
    |         on failure: stop, retry next cycle
    |
    +-- disconnectWifi()
```

## Configuration

All settings in `hardware/hardware_1.2/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `WIFI_SSID` | `"HubWiFi"` | WiFi network name |
| `WIFI_PASSWORD` | `"password_here"` | WiFi password |
| `API_BASE_URL` | `"https://api.beppp.cloud"` | Server API base URL |
| `BATCH_SIZE` | `50` | Entries per batch request |
| `MAX_BATCHES_PER_SESSION` | `20` | Max batches per wake cycle (cap: 1000 entries) |
| `USE_LTE` | `False` | Set `True` to use LTE instead of WiFi |

## Backend Endpoint

### `POST /webhook/batch-live-data`

Accepts a batch of historical entries from the SD card.

**Auth**: Same `Authorization: Bearer <token>` as `/webhook/live-data`.

**Request body**:
```json
{
    "battery_id": "1",
    "entries": [
        {"id": "1", "d": "2026-03-01", "tm": "14:30:00", "soc": 85.5, "v": 12.4, ...},
        {"id": "1", "d": "2026-03-01", "tm": "14:35:00", "soc": 84.2, "v": 12.3, ...}
    ]
}
```

**Limits**: Max 100 entries per request.

**Response**:
```json
{
    "status": "success",
    "stored": 50,
    "skipped": 0,
    "total_submitted": 50
}
```

The firmware checks for `"status": "success"` before advancing the FRAM pointer. Any other response (or network failure) causes a retry from the same position next cycle.

**Field mapping**: Uses the same `LIVE_DATA_FIELD_MAPPING` as the single-entry endpoint, including the new `aw` (awake_state) field.

## FRAM Line Tracking

The firmware tracks how many CSV data lines have been successfully sent using 5 bytes of FRAM (addresses 3-7, big-endian integer). This survives power loss and watchdog resets.

- On success: FRAM pointer advances past the sent lines
- On failure: FRAM pointer stays put, same lines are retried
- Corrupt CSV lines: skipped, pointer still advances past them
- Factory default (all zeros): starts from line 0 (beginning of file)

## Retry / Backoff

| Scenario | Retry interval |
|----------|---------------|
| Awake, send succeeded | 5 minutes |
| Awake, both SD + WiFi failed | 60 seconds (backoff) |
| Awake, WiFi failed but SD OK | 5 minutes (data safe on SD) |
| Asleep (nothing on) | 1 hour (RTC alarm wake) |
| Batch send failed mid-way | Next cycle, from same FRAM position |

## Database Migration

Migration `b7d4e1f23a56` adds `awake_state` (Integer, nullable) to the `livedata` table.

Run before deploying the updated API:
```bash
alembic upgrade head
```

## Testing

Test the batch endpoint against a running server:
```bash
TEST_BATTERY_SECRET=your_secret python scripts/test_batch_endpoint.py
```

Or with explicit arguments:
```bash
python scripts/test_batch_endpoint.py https://api.beppp.cloud 1 your_battery_secret
```

The test script covers: basic batch, empty/missing fields, auth rejection, 100-entry limit, corrupt entries, and full 50-entry batches.

## Files Changed

### Backend
| File | Change |
|------|--------|
| `models.py` | Added `awake_state` column to LiveData |
| `api/app/main.py` | Added `aw` field mapping + `POST /webhook/batch-live-data` endpoint |
| `alembic/versions/b7d4e1f23a56_...py` | Migration for awake_state column |

### Firmware
| File | Change |
|------|--------|
| `hardware/hardware_1.2/settings.py` | WiFi credentials, batch config, `USE_LTE` flag |
| `hardware/hardware_1.2/cebattery.py` | WiFi connect/disconnect, FRAM tracking, CSV parsing, batch sending, `aw` field, LTE guards |

### Test
| File | Description |
|------|-------------|
| `scripts/test_batch_endpoint.py` | 9 integration tests for the batch endpoint |

## Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| WiFi unavailable | Data logs to SD only, retries next cycle |
| SD card error | Skip batch send, send current reading directly |
| Corrupt CSV line | Skipped, FRAM pointer advances past it |
| Server error mid-batch | Stop sending, FRAM not advanced, retry next cycle |
| Large backlog (weeks offline) | Cleared over multiple cycles (max 1000 lines/cycle) |
| FRAM read error | Defaults to 0 (resend from beginning) |
| Power loss during send | FRAM only updated after server confirms (at-least-once delivery) |
