"""add_default_return_time_to_hub_settings

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-06-01 00:00:00.000000

Changes:
1. Add default_return_time (nullable String(5)) to hub_settings
   Stores a time string like "10:00" used to set the return time portion
   of due_back when creating battery rentals.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hub_settings', sa.Column('default_return_time', sa.String(5), nullable=True))


def downgrade() -> None:
    op.drop_column('hub_settings', 'default_return_time')
