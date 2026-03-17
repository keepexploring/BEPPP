"""add_max_recharges to cost_structures

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-16 12:00:00.000000

Changes:
1. Add max_recharges column to cost_structures table (NULL = unlimited)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cost_structures', sa.Column('max_recharges', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('cost_structures', 'max_recharges')
