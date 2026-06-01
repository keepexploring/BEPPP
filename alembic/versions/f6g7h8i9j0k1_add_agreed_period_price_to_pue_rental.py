"""add_agreed_period_price_to_pue_rental

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-06-01 00:00:00.000000

Changes:
1. Add agreed_period_price (nullable Float) to puerental
   Stores the flat price agreed at rental creation when a cost structure
   duration option has a fixed price configured (e.g. 500 for biweekly,
   900 for monthly). Used at return time to skip component-based recalculation.
"""
from typing import Union
from alembic import op
import sqlalchemy as sa


revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('puerental', sa.Column('agreed_period_price', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('puerental', 'agreed_period_price')
