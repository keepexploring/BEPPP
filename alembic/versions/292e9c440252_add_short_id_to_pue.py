"""add_short_id_to_pue

Revision ID: 292e9c440252
Revises: f6bb9eda646a
Create Date: 2026-01-13 15:31:25.856258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '292e9c440252'
down_revision: Union[str, Sequence[str], None] = 'f6bb9eda646a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add short_id column to productiveuseequipment table
    op.add_column('productiveuseequipment', sa.Column('short_id', sa.String(length=20), nullable=True))
    op.create_index(op.f('ix_productiveuseequipment_short_id'), 'productiveuseequipment', ['short_id'], unique=True)

    # Backfill existing PUE items with short_id
    op.execute("""
        UPDATE productiveuseequipment
        SET short_id = 'PUE-' || LPAD(pue_id::text, 4, '0')
        WHERE short_id IS NULL
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_productiveuseequipment_short_id'), table_name='productiveuseequipment')
    op.drop_column('productiveuseequipment', 'short_id')
