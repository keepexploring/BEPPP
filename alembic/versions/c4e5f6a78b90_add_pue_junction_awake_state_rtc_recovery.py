"""add_pue_junction_awake_state_rtc_recovery

Revision ID: c4e5f6a78b90
Revises: 7eb1613b119a
Create Date: 2026-03-05 12:00:00.000000

Combines three schema changes into one linear migration:
1. cost_structure_pue_items junction table
2. awake_state column on livedata
3. RTC corruption recovery columns on livedata (raw_timestamp, timestamp_reconstructed, is_final_batch)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e5f6a78b90'
down_revision: Union[str, Sequence[str], None] = '7eb1613b119a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. cost_structure_pue_items junction table
    op.create_table(
        'cost_structure_pue_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('structure_id', sa.Integer(), nullable=False),
        sa.Column('pue_id', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['structure_id'], ['cost_structures.structure_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pue_id'], ['productiveuseequipment.pue_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cs_pue_items_structure_id', 'cost_structure_pue_items', ['structure_id'])
    op.create_index('ix_cs_pue_items_pue_id', 'cost_structure_pue_items', ['pue_id'])

    # 2. awake_state column
    op.add_column('livedata', sa.Column('awake_state', sa.Integer(), nullable=True))

    # 3. RTC corruption recovery columns
    op.add_column('livedata', sa.Column('raw_timestamp', sa.String(100), nullable=True))
    op.add_column('livedata', sa.Column('timestamp_reconstructed', sa.Boolean(), nullable=True))
    op.add_column('livedata', sa.Column('is_final_batch', sa.Boolean(), nullable=True))


def downgrade() -> None:
    # 3. RTC corruption recovery columns
    op.drop_column('livedata', 'is_final_batch')
    op.drop_column('livedata', 'timestamp_reconstructed')
    op.drop_column('livedata', 'raw_timestamp')

    # 2. awake_state column
    op.drop_column('livedata', 'awake_state')

    # 1. cost_structure_pue_items junction table
    op.drop_index('ix_cs_pue_items_pue_id', table_name='cost_structure_pue_items')
    op.drop_index('ix_cs_pue_items_structure_id', table_name='cost_structure_pue_items')
    op.drop_table('cost_structure_pue_items')
