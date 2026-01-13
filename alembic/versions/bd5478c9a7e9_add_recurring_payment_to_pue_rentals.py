"""add_recurring_payment_to_pue_rentals

Revision ID: bd5478c9a7e9
Revises: 292e9c440252
Create Date: 2026-01-13 16:44:16.753865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd5478c9a7e9'
down_revision: Union[str, Sequence[str], None] = '292e9c440252'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add recurring payment fields to puerental table
    op.add_column('puerental', sa.Column('has_recurring_payment', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('puerental', sa.Column('recurring_payment_frequency', sa.String(50), nullable=True))  # 'monthly', 'weekly', 'daily'
    op.add_column('puerental', sa.Column('next_payment_due_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('puerental', sa.Column('last_payment_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('puerental', 'last_payment_date')
    op.drop_column('puerental', 'next_payment_due_date')
    op.drop_column('puerental', 'recurring_payment_frequency')
    op.drop_column('puerental', 'has_recurring_payment')
