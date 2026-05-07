"""add_updated_at_for_delta_sync

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-03-18 10:00:00.000000

Changes:
1. Add updated_at column to user, bepppbattery, puerental, notifications tables
2. Backfill updated_at with created_at values
3. Add indexes on updated_at for all 6 delta-sync target tables
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that need the updated_at column added
NEW_COLUMN_TABLES = ['user', 'bepppbattery', 'puerental', 'notifications']

# All tables that participate in delta sync (including those that already have updated_at)
ALL_DELTA_TABLES = ['user', 'bepppbattery', 'puerental', 'notifications', 'battery_rentals', 'job_cards']


def upgrade() -> None:
    # Step 1: Add updated_at column as nullable first
    for table in NEW_COLUMN_TABLES:
        op.add_column(table, sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    # Step 2: Backfill updated_at with created_at (COALESCE handles NULL created_at)
    for table in NEW_COLUMN_TABLES:
        # Quote table name to handle reserved words (e.g. "user")
        op.execute(f'UPDATE "{table}" SET updated_at = COALESCE(created_at, NOW()) WHERE updated_at IS NULL')

    # Step 3: Set NOT NULL and server default
    for table in NEW_COLUMN_TABLES:
        op.alter_column(table, 'updated_at', nullable=False, server_default=sa.func.now())

    # Step 4: Add indexes on updated_at for all delta-sync tables
    for table in ALL_DELTA_TABLES:
        op.create_index(f'ix_{table}_updated_at', table, ['updated_at'])


def downgrade() -> None:
    # Drop indexes
    for table in ALL_DELTA_TABLES:
        op.drop_index(f'ix_{table}_updated_at', table_name=table)

    # Drop columns
    for table in NEW_COLUMN_TABLES:
        op.drop_column(table, 'updated_at')
