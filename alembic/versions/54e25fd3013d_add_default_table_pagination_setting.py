"""add_default_table_pagination_setting

Revision ID: 54e25fd3013d
Revises: 0fdba945efbc
Create Date: 2025-12-22 15:42:33.602376

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54e25fd3013d'
down_revision: Union[str, Sequence[str], None] = '0fdba945efbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add default_table_rows_per_page column to hub_settings table."""
    op.add_column('hub_settings',
        sa.Column('default_table_rows_per_page', sa.Integer(), server_default='50', nullable=False))


def downgrade() -> None:
    """Remove default_table_rows_per_page column from hub_settings table."""
    op.drop_column('hub_settings', 'default_table_rows_per_page')
