"""add_battery_status_thresholds_to_hub_settings

Revision ID: 3ff9feb8478f
Revises: eefe705a3855
Create Date: 2025-12-22 21:54:19.939519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ff9feb8478f'
down_revision: Union[str, Sequence[str], None] = 'eefe705a3855'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add battery status threshold columns to hub_settings table."""
    op.add_column('hub_settings',
        sa.Column('battery_status_green_hours', sa.Integer, nullable=False, server_default='3'))
    op.add_column('hub_settings',
        sa.Column('battery_status_orange_hours', sa.Integer, nullable=False, server_default='8'))


def downgrade() -> None:
    """Remove battery status threshold columns from hub_settings table."""
    op.drop_column('hub_settings', 'battery_status_orange_hours')
    op.drop_column('hub_settings', 'battery_status_green_hours')
