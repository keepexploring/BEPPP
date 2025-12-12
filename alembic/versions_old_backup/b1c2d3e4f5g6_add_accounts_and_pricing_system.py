"""add accounts and pricing system

Revision ID: b1c2d3e4f5g6
Revises: 0c9a1f2202d4
Create Date: 2025-12-03 10:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, Sequence[str], None] = '0c9a1f2202d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add accounts, pricing, and settings tables."""

    # Import for conditional table creation
    from sqlalchemy import inspect
    from alembic import context

    # Get database connection
    conn = context.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create pue_types table (only if it doesn't exist)
    if 'pue_types' not in existing_tables:
        op.create_table(
            'pue_types',
            sa.Column('type_id', sa.Integer(), nullable=False),
            sa.Column('type_name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('hub_id', sa.Integer(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by'], ['user.user_id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('type_id'),
            sa.UniqueConstraint('type_name', 'hub_id', name='uq_pue_type_hub')
        )
        op.create_index('ix_pue_types_hub_id', 'pue_types', ['hub_id'])

    # Create pricing_configs table (only if it doesn't exist)
    if 'pricing_configs' not in existing_tables:
        op.create_table(
            'pricing_configs',
            sa.Column('pricing_id', sa.Integer(), nullable=False),
            sa.Column('hub_id', sa.Integer(), nullable=True),
            sa.Column('item_type', sa.String(length=50), nullable=False),  # 'battery_capacity', 'pue_item', 'pue_type'
            sa.Column('item_reference', sa.String(length=100), nullable=False),
            sa.Column('unit_type', sa.String(length=50), nullable=False),  # 'per_day', 'per_hour', 'per_kg', 'per_month', 'per_kwh'
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('pricing_id')
        )
        op.create_index('ix_pricing_configs_hub_id', 'pricing_configs', ['hub_id'])
        op.create_index('ix_pricing_configs_item', 'pricing_configs', ['item_type', 'item_reference'])

    # Create rental_duration_presets table (only if it doesn't exist)
    if 'rental_duration_presets' not in existing_tables:
        op.create_table(
            'rental_duration_presets',
            sa.Column('preset_id', sa.Integer(), nullable=False),
            sa.Column('hub_id', sa.Integer(), nullable=True),
            sa.Column('label', sa.String(length=50), nullable=False),
            sa.Column('duration_value', sa.Integer(), nullable=False),
            sa.Column('duration_unit', sa.String(length=20), nullable=False),  # 'hours', 'days', 'weeks'
            sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('preset_id')
        )
        op.create_index('ix_rental_duration_presets_hub_id', 'rental_duration_presets', ['hub_id'])

    # Create user_accounts table (only if it doesn't exist)
    if 'user_accounts' not in existing_tables:
        op.create_table(
            'user_accounts',
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('balance', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
            sa.Column('total_spent', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
            sa.Column('total_owed', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
            sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('account_id'),
            sa.UniqueConstraint('user_id')
        )
        op.create_index('ix_user_accounts_user_id', 'user_accounts', ['user_id'])

    # Create account_transactions table (only if it doesn't exist)
    if 'account_transactions' not in existing_tables:
        op.create_table(
            'account_transactions',
            sa.Column('transaction_id', sa.Integer(), nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('rental_id', sa.Integer(), nullable=True),
            sa.Column('transaction_type', sa.String(length=50), nullable=False),  # 'rental_charge', 'payment', 'credit_adjustment', 'debt_settlement'
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('balance_after', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['account_id'], ['user_accounts.account_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['rental_id'], ['rental.rentral_id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['created_by'], ['user.user_id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('transaction_id')
        )
        op.create_index('ix_account_transactions_account_id', 'account_transactions', ['account_id'])
        op.create_index('ix_account_transactions_rental_id', 'account_transactions', ['rental_id'])
        op.create_index('ix_account_transactions_created_at', 'account_transactions', ['created_at'])

    # Create hub_settings table (only if it doesn't exist)
    if 'hub_settings' not in existing_tables:
        op.create_table(
            'hub_settings',
            sa.Column('setting_id', sa.Integer(), nullable=False),
            sa.Column('hub_id', sa.Integer(), nullable=True),
            sa.Column('debt_notification_threshold', sa.Numeric(precision=10, scale=2), server_default='-100.00', nullable=False),
            sa.Column('default_currency', sa.String(length=3), server_default='USD', nullable=False),
            sa.Column('other_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('setting_id'),
            sa.UniqueConstraint('hub_id')
        )
        op.create_index('ix_hub_settings_hub_id', 'hub_settings', ['hub_id'])

    # Add new columns to rental table
    op.add_column('rental', sa.Column('rental_unique_id', sa.String(length=50), nullable=True))
    op.add_column('rental', sa.Column('payment_status', sa.String(length=20), server_default='unpaid', nullable=False))
    op.add_column('rental', sa.Column('total_cost_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('rental', sa.Column('amount_paid', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False))
    op.add_column('rental', sa.Column('amount_owed', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False))

    # Create unique index on rental_unique_id
    op.create_index('ix_rental_unique_id', 'rental', ['rental_unique_id'], unique=True)

    # Add pue_type_id to productiveuseequipment table
    op.add_column('productiveuseequipment', sa.Column('pue_type_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_pue_type', 'productiveuseequipment', 'pue_types', ['pue_type_id'], ['type_id'], ondelete='SET NULL')
    op.create_index('ix_pue_type_id', 'productiveuseequipment', ['pue_type_id'])

    # Insert default rental duration presets (global)
    op.execute("""
        INSERT INTO rental_duration_presets (label, duration_value, duration_unit, sort_order, hub_id)
        VALUES
            ('1 Day', 1, 'days', 1, NULL),
            ('2 Days', 2, 'days', 2, NULL),
            ('3 Days', 3, 'days', 3, NULL),
            ('1 Week', 1, 'weeks', 4, NULL),
            ('2 Weeks', 2, 'weeks', 5, NULL),
            ('4 Weeks', 4, 'weeks', 6, NULL)
    """)

    # Insert default hub_settings for existing hubs
    op.execute("""
        INSERT INTO hub_settings (hub_id, debt_notification_threshold, default_currency)
        SELECT hub_id, -100.00, 'USD' FROM solarhub
    """)

    # Insert global hub_settings (NULL hub_id)
    op.execute("""
        INSERT INTO hub_settings (hub_id, debt_notification_threshold, default_currency)
        VALUES (NULL, -100.00, 'USD')
    """)


def downgrade() -> None:
    """Downgrade schema - Remove accounts and pricing tables."""

    # Drop foreign key and index from productiveuseequipment table
    op.drop_index('ix_pue_type_id', 'productiveuseequipment')
    op.drop_constraint('fk_pue_type', 'productiveuseequipment', type_='foreignkey')
    op.drop_column('productiveuseequipment', 'pue_type_id')

    # Drop new columns from rental table
    op.drop_index('ix_rental_unique_id', 'rental')
    op.drop_column('rental', 'amount_owed')
    op.drop_column('rental', 'amount_paid')
    op.drop_column('rental', 'total_cost_breakdown')
    op.drop_column('rental', 'payment_status')
    op.drop_column('rental', 'rental_unique_id')

    # Drop tables
    op.drop_table('hub_settings')
    op.drop_table('account_transactions')
    op.drop_table('user_accounts')
    op.drop_table('rental_duration_presets')
    op.drop_table('pricing_configs')
    op.drop_table('pue_types')
