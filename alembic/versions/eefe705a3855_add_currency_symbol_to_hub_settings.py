"""add_currency_symbol_to_hub_settings

Revision ID: eefe705a3855
Revises: 54e25fd3013d
Create Date: 2025-12-22 17:01:33.060935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eefe705a3855'
down_revision: Union[str, Sequence[str], None] = '54e25fd3013d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add currency_symbol column to hub_settings table."""
    op.add_column('hub_settings',
        sa.Column('currency_symbol', sa.String(10), nullable=True))


def downgrade() -> None:
    """Remove currency_symbol column from hub_settings table."""
    op.drop_column('hub_settings', 'currency_symbol')
