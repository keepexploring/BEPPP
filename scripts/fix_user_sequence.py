#!/usr/bin/env python3
"""
Fix PostgreSQL sequence for user table.

This script resets the user_id sequence to match the current max user_id in the table.
Run this when you get "duplicate key value violates unique constraint" errors.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from project
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine

def fix_user_sequence():
    """Reset the user_id sequence to the maximum existing user_id + 1"""
    with engine.connect() as conn:
        # Get the maximum user_id currently in the table
        result = conn.execute(text('SELECT MAX(user_id) FROM "user"'))
        max_id = result.scalar()

        if max_id is None:
            max_id = 0

        # Set the sequence to max_id + 1
        next_id = max_id + 1
        conn.execute(text(f"SELECT setval('user_user_id_seq', {next_id}, false)"))
        conn.commit()

        print(f"✅ Fixed user_id sequence!")
        print(f"   Current max user_id: {max_id}")
        print(f"   Next user_id will be: {next_id}")

if __name__ == "__main__":
    try:
        fix_user_sequence()
    except Exception as e:
        print(f"❌ Error fixing sequence: {e}")
        sys.exit(1)
