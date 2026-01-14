"""add_recurring_payment_to_cost_components

Revision ID: d30fceecdec1
Revises: bd5478c9a7e9
Create Date: 2026-01-13 16:57:13.606511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd30fceecdec1'
down_revision: Union[str, Sequence[str], None] = 'bd5478c9a7e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add recurring payment fields to cost_components table
    op.add_column('cost_components', sa.Column('is_recurring_payment', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('cost_components', sa.Column('recurring_interval', sa.Numeric(5, 2), nullable=True))  # e.g., 1.0, 2.0, 0.5


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cost_components', 'recurring_interval')
    op.drop_column('cost_components', 'is_recurring_payment')
