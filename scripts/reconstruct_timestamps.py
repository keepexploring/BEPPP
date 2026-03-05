#!/usr/bin/env python3
"""
Reconstruct corrupt RTC timestamps for battery live data.

When the DS3231 RTC is corrupted (e.g. WDT reset writing 0xFF to registers),
timestamps are stored as NULL with the raw corrupt values saved in raw_timestamp.

This script reconstructs those NULL timestamps by:
1. Grouping entries into upload sessions (by created_at proximity)
2. Finding sessions with a valid anchor (is_final_batch=True)
3. Walking backwards from the anchor, spacing entries by awake_state interval

Usage:
    # Dry run for one battery
    python scripts/reconstruct_timestamps.py --dry-run --battery-id 1

    # Live run for one battery
    python scripts/reconstruct_timestamps.py --battery-id 1

    # Dry run for all batteries with NULL timestamps
    python scripts/reconstruct_timestamps.py --dry-run

    # Live run for all
    python scripts/reconstruct_timestamps.py
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

# Add project root to path so we can import models/database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from models import LiveData

# Intervals between data points based on awake state
AWAKE_INTERVAL = timedelta(minutes=5)
ASLEEP_INTERVAL = timedelta(minutes=60)

# Max gap between entries to consider them part of the same upload session.
# Entries arriving within 30 seconds of each other are in the same session.
SESSION_GAP_THRESHOLD = timedelta(seconds=30)


def get_db_session():
    """Create a database session using the app's DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set.")
        print("Set it in .env or export it before running this script.")
        sys.exit(1)

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(database_url, poolclass=NullPool, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def group_into_sessions(entries):
    """Group entries into upload sessions based on created_at proximity.

    Entries with created_at within SESSION_GAP_THRESHOLD of each other
    are considered part of the same upload session.
    """
    if not entries:
        return []

    sessions = []
    current_session = [entries[0]]

    for entry in entries[1:]:
        prev = current_session[-1]
        gap = entry.created_at - prev.created_at
        if gap <= SESSION_GAP_THRESHOLD:
            current_session.append(entry)
        else:
            sessions.append(current_session)
            current_session = [entry]

    sessions.append(current_session)
    return sessions


def get_interval_for_entry(entry):
    """Return the time interval to subtract when walking backwards."""
    if entry.awake_state == 1:
        return AWAKE_INTERVAL
    # Default to asleep interval (conservative) for awake_state=0 or NULL
    return ASLEEP_INTERVAL


def reconstruct_session(session_entries, dry_run=False):
    """Reconstruct NULL timestamps for a single upload session.

    Returns (reconstructed_count, skipped_reason_or_None).
    """
    # Check if session has a valid anchor (is_final_batch=True)
    has_final_batch = any(e.is_final_batch for e in session_entries)
    if not has_final_batch:
        return 0, "no is_final_batch=True (incomplete session, skipped)"

    # Find the anchor: last entry with is_final_batch=True
    # (entries are ordered by created_at ASC, id ASC — last = newest)
    anchor_entry = None
    for entry in reversed(session_entries):
        if entry.is_final_batch:
            anchor_entry = entry
            break

    # The anchor's real timestamp = its created_at (server arrival time)
    anchor_idx = session_entries.index(anchor_entry)

    # Walk backwards from the anchor
    reconstructed_count = 0

    # Set anchor timestamp if NULL
    if anchor_entry.timestamp is None:
        anchor_entry.timestamp = anchor_entry.created_at
        anchor_entry.timestamp_reconstructed = True
        reconstructed_count += 1
        if dry_run:
            print(f"    [DRY RUN] Entry {anchor_entry.id}: "
                  f"NULL -> {anchor_entry.created_at.isoformat()} (anchor, raw: {anchor_entry.raw_timestamp})")

    # Walk backwards from anchor through earlier entries
    current_ts = anchor_entry.timestamp
    for i in range(anchor_idx - 1, -1, -1):
        entry = session_entries[i]

        if entry.timestamp is not None:
            # Valid timestamp — use as new reference point
            current_ts = entry.timestamp
            continue

        # Calculate reconstructed timestamp
        interval = get_interval_for_entry(entry)
        new_ts = current_ts - interval
        current_ts = new_ts

        if dry_run:
            aw_label = "awake" if entry.awake_state == 1 else "asleep"
            print(f"    [DRY RUN] Entry {entry.id}: "
                  f"NULL -> {new_ts.isoformat()} ({aw_label}, -{interval}, raw: {entry.raw_timestamp})")
        else:
            entry.timestamp = new_ts
            entry.timestamp_reconstructed = True

        reconstructed_count += 1

    # Walk forward from anchor through any later entries (rare, but handle it)
    current_ts = anchor_entry.timestamp
    for i in range(anchor_idx + 1, len(session_entries)):
        entry = session_entries[i]

        if entry.timestamp is not None:
            current_ts = entry.timestamp
            continue

        interval = get_interval_for_entry(session_entries[i - 1])
        new_ts = current_ts + interval
        current_ts = new_ts

        if dry_run:
            aw_label = "awake" if session_entries[i - 1].awake_state == 1 else "asleep"
            print(f"    [DRY RUN] Entry {entry.id}: "
                  f"NULL -> {new_ts.isoformat()} ({aw_label}, +{interval}, raw: {entry.raw_timestamp})")
        else:
            entry.timestamp = new_ts
            entry.timestamp_reconstructed = True

        reconstructed_count += 1

    return reconstructed_count, None


def reconstruct_battery(db, battery_id, dry_run=False):
    """Reconstruct timestamps for a single battery."""
    entries = (
        db.query(LiveData)
        .filter(LiveData.battery_id == battery_id)
        .order_by(LiveData.created_at.asc(), LiveData.id.asc())
        .all()
    )

    if not entries:
        print(f"  Battery {battery_id}: no data found")
        return 0

    null_count = sum(1 for e in entries if e.timestamp is None)
    if null_count == 0:
        print(f"  Battery {battery_id}: {len(entries)} entries, all timestamps valid")
        return 0

    print(f"  Battery {battery_id}: {len(entries)} entries, {null_count} with NULL timestamps")

    sessions = group_into_sessions(entries)
    print(f"    Found {len(sessions)} upload session(s)")

    total_reconstructed = 0
    for idx, session_entries in enumerate(sessions):
        null_in_session = sum(1 for e in session_entries if e.timestamp is None)
        if null_in_session == 0:
            continue

        print(f"    Session {idx + 1}: {len(session_entries)} entries, "
              f"{null_in_session} NULL timestamps, "
              f"created_at range: {session_entries[0].created_at.isoformat()} - "
              f"{session_entries[-1].created_at.isoformat()}")

        count, skip_reason = reconstruct_session(session_entries, dry_run=dry_run)
        if skip_reason:
            print(f"      Skipped: {skip_reason}")
        else:
            total_reconstructed += count

    if not dry_run and total_reconstructed > 0:
        db.commit()
        print(f"    Committed {total_reconstructed} reconstructed timestamps")

    return total_reconstructed


def main():
    parser = argparse.ArgumentParser(
        description="Reconstruct corrupt RTC timestamps for battery live data."
    )
    parser.add_argument(
        "--battery-id",
        type=str,
        default=None,
        help="Battery ID to process (omit for all batteries with NULL timestamps)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to database"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  RTC Timestamp Reconstruction")
    print("=" * 60)
    if args.dry_run:
        print("  MODE: DRY RUN (no changes will be written)")
    else:
        print("  MODE: LIVE (changes will be committed)")
    print()

    db = get_db_session()

    try:
        if args.battery_id:
            battery_ids = [args.battery_id]
        else:
            # Find all batteries that have NULL timestamps
            results = (
                db.query(LiveData.battery_id)
                .filter(LiveData.timestamp.is_(None))
                .distinct()
                .all()
            )
            battery_ids = [r[0] for r in results]

            if not battery_ids:
                print("  No batteries found with NULL timestamps.")
                return

            print(f"  Found {len(battery_ids)} battery(ies) with NULL timestamps: "
                  f"{', '.join(str(b) for b in battery_ids)}")
            print()

        grand_total = 0
        for bid in battery_ids:
            count = reconstruct_battery(db, bid, dry_run=args.dry_run)
            grand_total += count
            print()

        print("=" * 60)
        print(f"  Total reconstructed: {grand_total}")
        if args.dry_run and grand_total > 0:
            print("  Run without --dry-run to apply changes.")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
