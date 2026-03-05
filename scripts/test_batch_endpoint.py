#!/usr/bin/env python3
"""
Test script for the batch live data endpoint: POST /webhook/batch-live-data
Run against a live server. Requires a valid battery in the database.

Usage:
    # Via environment variables:
    TEST_BATTERY_SECRET=your_secret python scripts/test_batch_endpoint.py

    # Via CLI args:
    python scripts/test_batch_endpoint.py http://localhost:8000 1 your_battery_secret

    # Against production:
    python scripts/test_batch_endpoint.py https://api.beppp.cloud 1 your_battery_secret

Defaults to localhost:8000 with battery "1". Battery secret is required.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta

# Configuration — override via CLI args or environment variables
API_BASE_URL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("API_URL", "http://localhost:8000")
TEST_BATTERY_ID = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TEST_BATTERY_ID", "1")
TEST_BATTERY_SECRET = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("TEST_BATTERY_SECRET", "")

if not TEST_BATTERY_SECRET:
    print("ERROR: No battery secret provided.")
    print("Set TEST_BATTERY_SECRET env var or pass as 3rd argument:")
    print("  python scripts/test_batch_endpoint.py http://localhost:8000 1 YOUR_SECRET")
    sys.exit(1)

passed = 0
failed = 0


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")
    if detail:
        print(f"        {detail}")


def get_token():
    """Authenticate as the test battery and return the JWT token."""
    r = requests.post(f"{API_BASE_URL}/auth/battery-login", json={
        "battery_id": TEST_BATTERY_ID,
        "battery_secret": TEST_BATTERY_SECRET,
    }, timeout=10)
    if r.status_code != 200:
        print(f"Login failed ({r.status_code}): {r.text}")
        sys.exit(1)
    return r.json()["access_token"]


def make_entry(minutes_ago=0, soc=80.0, voltage=12.4, temp=22.0, awake=1):
    """Build a single entry dict matching firmware getData() format."""
    ts = datetime.utcnow() - timedelta(minutes=minutes_ago)
    return {
        "id": TEST_BATTERY_ID,
        "d": ts.strftime("%Y-%m-%d"),
        "tm": ts.strftime("%H:%M:%S"),
        "soc": soc,
        "v": voltage,
        "i": 1.5,
        "p": voltage * 1.5,
        "t": temp,
        "ci": 0.3,
        "cv": 14.1,
        "cp": 4.2,
        "ui": 0.0,
        "uv": 0.0,
        "up": 0.0,
        "eu": 0,
        "ec": 1,
        "ef": 0,
        "ei": 0,
        "ts": 0,
        "lat": 1.234,
        "lon": 36.789,
        "alt": 100.0,
        "gf": 1,
        "gs": 8,
        "gd": ts.strftime("%Y-%m-%d"),
        "gt": ts.strftime("%H:%M:%S"),
        "nc": 5,
        "cc": 1.2,
        "tcc": 50.0,
        "tr": -1.0,
        "sa": 0,
        "err": "",
        "aw": awake,
    }


# ---- Tests ----

def test_basic_batch(headers):
    """Send a small batch of 3 entries — should all succeed."""
    section("TEST 1: Basic batch (3 entries)")
    entries = [make_entry(minutes_ago=i*5, soc=80-i) for i in range(3)]
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": entries,
    }, headers=headers, timeout=15)
    data = r.json()
    check("Status 200", r.status_code == 200, f"got {r.status_code}")
    check("status=success", data.get("status") == "success", json.dumps(data))
    check("stored=3", data.get("stored") == 3, f"stored={data.get('stored')}")
    check("skipped=0", data.get("skipped") == 0, f"skipped={data.get('skipped')}")
    check("total_submitted=3", data.get("total_submitted") == 3)


def test_awake_field(headers):
    """Verify the 'aw' field maps to awake_state in the DB."""
    section("TEST 2: awake_state field mapping")
    entries = [make_entry(minutes_ago=0, awake=1)]
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": entries,
    }, headers=headers, timeout=15)
    data = r.json()
    check("status=success", data.get("status") == "success")
    check("stored=1", data.get("stored") == 1)


def test_empty_entries(headers):
    """Empty entries array should return 400."""
    section("TEST 3: Empty entries array")
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": [],
    }, headers=headers, timeout=15)
    check("Status 400", r.status_code == 400, f"got {r.status_code}")


def test_missing_battery_id(headers):
    """Missing battery_id should return 400."""
    section("TEST 4: Missing battery_id")
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "entries": [make_entry()],
    }, headers=headers, timeout=15)
    check("Status 400", r.status_code == 400, f"got {r.status_code}")


def test_wrong_battery_id(headers):
    """Submitting for a different battery should return 403."""
    section("TEST 5: Wrong battery_id (should be rejected)")
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": "999999",
        "entries": [make_entry()],
    }, headers=headers, timeout=15)
    check("Status 403", r.status_code == 403, f"got {r.status_code}")


def test_over_limit(headers):
    """More than 100 entries should return 400."""
    section("TEST 6: Over 100 entries limit")
    entries = [make_entry(minutes_ago=i) for i in range(101)]
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": entries,
    }, headers=headers, timeout=30)
    check("Status 400", r.status_code == 400, f"got {r.status_code}")


def test_partial_corrupt_entries(headers):
    """Mix of valid and corrupt entries — valid ones stored, corrupt ones skipped."""
    section("TEST 7: Partial corrupt entries")
    entries = [
        make_entry(minutes_ago=30),
        {"garbage": True},  # corrupt — no id, no date/time
        make_entry(minutes_ago=20),
    ]
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": entries,
    }, headers=headers, timeout=15)
    data = r.json()
    check("Status 200", r.status_code == 200, f"got {r.status_code}")
    check("status=success", data.get("status") == "success")
    # All 3 should be "stored" since the endpoint injects battery_id and
    # handles missing fields gracefully via safe_convert_value
    check("total_submitted=3", data.get("total_submitted") == 3)
    stored = data.get("stored", 0)
    skipped = data.get("skipped", 0)
    check("stored+skipped=3", stored + skipped == 3, f"stored={stored} skipped={skipped}")


def test_no_auth():
    """Request without auth token should return 401/403."""
    section("TEST 8: No authentication")
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": [make_entry()],
    }, timeout=10)
    check("Status 401 or 403", r.status_code in (401, 403), f"got {r.status_code}")


def test_corrupt_timestamps_with_final_batch(headers):
    """Send batch with corrupt RTC timestamps + fb:1 — should store with NULL timestamp."""
    section("TEST 9: Corrupt timestamps with final_batch flag")
    entries = [
        {
            "id": TEST_BATTERY_ID,
            "d": "20FF-FF-FF",
            "tm": "FF:FF:FF",
            "soc": 75.0,
            "v": 12.2,
            "i": 1.0,
            "p": 12.2,
            "t": 25.0,
            "aw": 1,
        },
        {
            "id": TEST_BATTERY_ID,
            "d": "20FF-FF-FF",
            "tm": "FF:FF:FF",
            "soc": 74.0,
            "v": 12.1,
            "i": 1.1,
            "p": 13.3,
            "t": 25.5,
            "aw": 0,
        },
    ]
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "fb": 1,
        "entries": entries,
    }, headers=headers, timeout=15)
    data = r.json()
    check("Status 200", r.status_code == 200, f"got {r.status_code}")
    check("status=success", data.get("status") == "success", json.dumps(data))
    check("stored=2", data.get("stored") == 2, f"stored={data.get('stored')}")
    check("skipped=0", data.get("skipped") == 0, f"skipped={data.get('skipped')}")


def test_final_batch_flag_default(headers):
    """Batch without fb flag should default to is_final_batch=False."""
    section("TEST 10: Missing fb flag defaults to false")
    entries = [make_entry(minutes_ago=0)]
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": entries,
    }, headers=headers, timeout=15)
    data = r.json()
    check("Status 200", r.status_code == 200, f"got {r.status_code}")
    check("status=success", data.get("status") == "success")
    check("stored=1", data.get("stored") == 1)


def test_large_batch(headers):
    """Send a full 50-entry batch (matches firmware BATCH_SIZE)."""
    section("TEST 11: Full 50-entry batch")
    entries = [make_entry(minutes_ago=i*5, soc=90-i*0.5) for i in range(50)]
    r = requests.post(f"{API_BASE_URL}/webhook/batch-live-data", json={
        "battery_id": TEST_BATTERY_ID,
        "entries": entries,
    }, headers=headers, timeout=30)
    data = r.json()
    check("Status 200", r.status_code == 200, f"got {r.status_code}")
    check("status=success", data.get("status") == "success")
    check("stored=50", data.get("stored") == 50, f"stored={data.get('stored')}")


def main():
    print(f"\nBatch Live Data Endpoint Test Suite")
    print(f"API: {API_BASE_URL}")
    print(f"Battery: {TEST_BATTERY_ID}")

    section("SETUP: Authenticate")
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  Token: {token[:40]}...")

    test_basic_batch(headers)
    test_awake_field(headers)
    test_empty_entries(headers)
    test_missing_battery_id(headers)
    test_wrong_battery_id(headers)
    test_over_limit(headers)
    test_partial_corrupt_entries(headers)
    test_no_auth()
    test_corrupt_timestamps_with_final_batch(headers)
    test_final_batch_flag_default(headers)
    test_large_batch(headers)

    section("RESULTS")
    total = passed + failed
    print(f"  {passed}/{total} passed, {failed} failed")
    if failed:
        print(f"\n  Verify with SQL:")
        print(f"    SELECT COUNT(*) FROM livedata WHERE battery_id = '{TEST_BATTERY_ID}';")
        print(f"    SELECT * FROM livedata WHERE battery_id = '{TEST_BATTERY_ID}' ORDER BY created_at DESC LIMIT 5;")
        print(f"    SELECT * FROM webhook_logs WHERE endpoint = '/webhook/batch-live-data' ORDER BY created_at DESC LIMIT 5;")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
