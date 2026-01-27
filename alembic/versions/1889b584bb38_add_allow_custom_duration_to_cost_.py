"""add_allow_custom_duration_to_cost_structures

Revision ID: 1889b584bb38
Revises: ff7c9c33882f
Create Date: 2026-01-16 12:24:19.047983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1889b584bb38'
down_revision: Union[str, Sequence[str], None] = 'ff7c9c33882f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add allow_custom_duration column to cost_structures table."""
    op.add_column('cost_structures', sa.Column('allow_custom_duration', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    """Remove allow_custom_duration column from cost_structures table."""
    op.drop_column('cost_structures', 'allow_custom_duration')
