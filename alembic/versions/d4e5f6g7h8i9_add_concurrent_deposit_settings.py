"""add_concurrent_deposit_settings

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-05-13 10:00:00.000000

Changes:
1. Add battery_concurrent_deposit (default False) to hub_settings
   When True: charge a deposit for each additional battery rented concurrently.
   When False (default): only charge the deposit once per customer, regardless
   of how many rentals they make sequentially.
2. Add pue_concurrent_deposit (default True) to hub_settings
   Same logic for PUE items.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hub_settings', sa.Column('battery_concurrent_deposit', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('hub_settings', sa.Column('pue_concurrent_deposit', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('hub_settings', 'pue_concurrent_deposit')
    op.drop_column('hub_settings', 'battery_concurrent_deposit')
