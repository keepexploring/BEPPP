"""add_enhanced_payment_system

Revision ID: d8e9f0g1h2i3
Revises: c7d8e9f0g1h2
Create Date: 2025-12-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd8e9f0g1h2i3'
down_revision = 'c7d8e9f0g1h2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields to rental table for enhanced payment system
    op.add_column('rental', sa.Column('deposit_returned', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('rental', sa.Column('deposit_returned_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('rental', sa.Column('payment_method', sa.String(length=50), nullable=True))
    op.add_column('rental', sa.Column('kwh_usage_start', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('kwh_usage_end', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('kwh_usage_total', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('standing_charge', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('kwh_rate', sa.Float(), nullable=True))

    # Create deposit_presets table
    op.create_table('deposit_presets',
        sa.Column('preset_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hub_id', sa.BigInteger(), nullable=True),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('item_reference', sa.String(length=100), nullable=False),
        sa.Column('deposit_amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('preset_id')
    )

    # Create indexes for better query performance
    op.create_index('ix_deposit_presets_hub_id', 'deposit_presets', ['hub_id'])
    op.create_index('ix_deposit_presets_item', 'deposit_presets', ['item_type', 'item_reference'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_deposit_presets_item', table_name='deposit_presets')
    op.drop_index('ix_deposit_presets_hub_id', table_name='deposit_presets')

    # Drop deposit_presets table
    op.drop_table('deposit_presets')

    # Remove columns from rental table
    op.drop_column('rental', 'kwh_rate')
    op.drop_column('rental', 'standing_charge')
    op.drop_column('rental', 'kwh_usage_total')
    op.drop_column('rental', 'kwh_usage_end')
    op.drop_column('rental', 'kwh_usage_start')
    op.drop_column('rental', 'payment_method')
    op.drop_column('rental', 'deposit_returned_date')
    op.drop_column('rental', 'deposit_returned')
