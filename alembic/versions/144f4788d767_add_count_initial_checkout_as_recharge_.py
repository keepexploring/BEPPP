"""Add count_initial_checkout_as_recharge to cost_structures

Revision ID: 144f4788d767
Revises: 3c8962edbe42
Create Date: 2026-01-12 13:03:14.932507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '144f4788d767'
down_revision: Union[str, Sequence[str], None] = '3c8962edbe42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add count_initial_checkout_as_recharge field to cost_structures
    op.add_column('cost_structures', sa.Column('count_initial_checkout_as_recharge', sa.Boolean(), server_default='false', nullable=False))
    # Drop the old charge_known_costs_upfront column from battery config if it exists
    # Using raw SQL because Alembic doesn't support IF EXISTS for drop_column
    op.execute("ALTER TABLE cost_structure_battery_config DROP COLUMN IF EXISTS charge_known_costs_upfront")


def downgrade() -> None:
    """Downgrade schema."""
    # Restore charge_known_costs_upfront
    op.add_column('cost_structure_battery_config', sa.Column('charge_known_costs_upfront', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
    # Drop count_initial_checkout_as_recharge
    op.drop_column('cost_structures', 'count_initial_checkout_as_recharge')
