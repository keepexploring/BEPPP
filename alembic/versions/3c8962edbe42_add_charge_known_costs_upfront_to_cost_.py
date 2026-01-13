"""Add charge_known_costs_upfront to cost_structure_battery_config

Revision ID: 3c8962edbe42
Revises: f177f72b3403
Create Date: 2026-01-06 21:32:26.338659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c8962edbe42'
down_revision: Union[str, Sequence[str], None] = 'f177f72b3403'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add charge_known_costs_upfront column to cost_structure_battery_config
    op.add_column('cost_structure_battery_config',
        sa.Column('charge_known_costs_upfront', sa.Boolean(), server_default='false', nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove charge_known_costs_upfront column from cost_structure_battery_config
    op.drop_column('cost_structure_battery_config', 'charge_known_costs_upfront')
