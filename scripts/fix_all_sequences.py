#!/usr/bin/env python3
"""
Fix all PostgreSQL sequences in the database.

This script resets all table sequences to match the current max ID values.
Run this during deployment or after importing data to prevent duplicate key errors.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from project
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from database import engine, Base

def fix_all_sequences():
    """Reset all primary key sequences to match the maximum existing ID values"""

    # Get all table names from the models
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    fixed_count = 0

    with engine.connect() as conn:
        for table_name in tables:
            # Get primary key columns for this table
            pk_columns = inspector.get_pk_constraint(table_name)

            if not pk_columns or not pk_columns.get('constrained_columns'):
                continue

            # Assuming single column primary key (which is our case)
            pk_column = pk_columns['constrained_columns'][0]

            # Check if this is an integer auto-increment column
            columns = inspector.get_columns(table_name)
            pk_col_info = next((c for c in columns if c['name'] == pk_column), None)

            if not pk_col_info or 'integer' not in str(pk_col_info.get('type', '')).lower():
                continue

            # Construct sequence name (PostgreSQL convention: tablename_columnname_seq)
            sequence_name = f"{table_name}_{pk_column}_seq"

            try:
                # Check if sequence exists
                seq_check = conn.execute(text(
                    f"SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = '{sequence_name}'"
                ))

                if not seq_check.fetchone():
                    continue  # Sequence doesn't exist, skip

                # Get the maximum ID currently in the table
                result = conn.execute(text(f'SELECT MAX({pk_column}) FROM "{table_name}"'))
                max_id = result.scalar()

                if max_id is None:
                    max_id = 0

                # Set the sequence to max_id + 1
                next_id = max_id + 1
                conn.execute(text(f"SELECT setval('{sequence_name}', {next_id}, false)"))

                print(f"✅ Fixed {table_name}.{pk_column} sequence (max: {max_id}, next: {next_id})")
                fixed_count += 1

            except Exception as e:
                print(f"⚠️  Skipped {table_name}.{pk_column}: {e}")
                continue

        conn.commit()

    print(f"\n🎉 Successfully fixed {fixed_count} sequence(s)!")
    return fixed_count

if __name__ == "__main__":
    try:
        print("🔧 Fixing all database sequences...\n")
        fix_all_sequences()
    except Exception as e:
        print(f"\n❌ Error fixing sequences: {e}")
        sys.exit(1)
