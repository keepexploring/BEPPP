"""add_late_fee_fields_to_cost_components

Revision ID: 8925623423e9
Revises: 144f4788d767
Create Date: 2026-01-12 13:16:25.573405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8925623423e9'
down_revision: Union[str, Sequence[str], None] = '144f4788d767'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add late fee configuration fields to cost_components
    op.add_column('cost_components', sa.Column('late_fee_action', sa.String(50), server_default='continue', nullable=False))
    op.add_column('cost_components', sa.Column('late_fee_rate', sa.Float, nullable=True))
    op.add_column('cost_components', sa.Column('late_fee_grace_days', sa.Integer, server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove late fee configuration fields from cost_components
    op.drop_column('cost_components', 'late_fee_grace_days')
    op.drop_column('cost_components', 'late_fee_rate')
    op.drop_column('cost_components', 'late_fee_action')
