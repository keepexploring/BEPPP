"""add_return_survey_required_to_solarhub

Revision ID: 0815ef71fd30
Revises: 6c27aa6b72d3
Create Date: 2026-01-21 16:02:20.767742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0815ef71fd30'
down_revision: Union[str, Sequence[str], None] = '6c27aa6b72d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add return_survey_required field to solarhub table
    op.add_column('solarhub', sa.Column('return_survey_required', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove return_survey_required field
    op.drop_column('solarhub', 'return_survey_required')
