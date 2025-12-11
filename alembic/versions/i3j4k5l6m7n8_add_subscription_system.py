"""add subscription system

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2025-12-05 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'i3j4k5l6m7n8'
down_revision = 'h2i3j4k5l6m7'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add subscription package system:
    1. subscription_packages - Define subscription plans
    2. subscription_package_items - Items included in each package
    3. user_subscriptions - Active subscriptions for users
    """

    # ========================================================================
    # 1. Create subscription_packages table
    # ========================================================================
    op.create_table(
        'subscription_packages',
        sa.Column('package_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hub_id', sa.BigInteger(), nullable=True),
        sa.Column('package_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('billing_period', sa.String(length=20), nullable=False),  # 'daily', 'weekly', 'monthly', 'yearly'
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('max_concurrent_batteries', sa.Integer(), nullable=True),  # Max batteries at once (null = unlimited)
        sa.Column('max_concurrent_pue', sa.Integer(), nullable=True),  # Max PUE items at once (null = unlimited)
        sa.Column('included_kwh', sa.Float(), nullable=True),  # Included kWh per billing period (null = unlimited)
        sa.Column('overage_rate_kwh', sa.Float(), nullable=True),  # Rate per kWh over included amount
        sa.Column('auto_renew', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('package_id'),
        sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE')
    )
    op.create_index('idx_subscription_packages_hub', 'subscription_packages', ['hub_id'])

    # ========================================================================
    # 2. Create subscription_package_items table
    # ========================================================================
    op.create_table(
        'subscription_package_items',
        sa.Column('item_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),  # 'battery', 'battery_capacity', 'pue', 'pue_type', 'pue_item'
        sa.Column('item_reference', sa.String(length=100), nullable=False),  # 'all' or specific ID
        sa.Column('quantity_limit', sa.Integer(), nullable=True),  # How many of this type (null = unlimited)
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('item_id'),
        sa.ForeignKeyConstraint(['package_id'], ['subscription_packages.package_id'], ondelete='CASCADE')
    )
    op.create_index('idx_subscription_items_package', 'subscription_package_items', ['package_id'])

    # ========================================================================
    # 3. Create user_subscriptions table
    # ========================================================================
    op.create_table(
        'user_subscriptions',
        sa.Column('subscription_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),  # null = active indefinitely
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),  # 'active', 'paused', 'cancelled', 'expired'
        sa.Column('auto_renew', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('kwh_used_current_period', sa.Float(), server_default='0', nullable=False),
        sa.Column('period_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('subscription_id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['package_id'], ['subscription_packages.package_id'], ondelete='RESTRICT')
    )
    op.create_index('idx_user_subscriptions_user', 'user_subscriptions', ['user_id'])
    op.create_index('idx_user_subscriptions_status', 'user_subscriptions', ['status'])

    # ========================================================================
    # 4. Add subscription_id to rental table (optional link)
    # ========================================================================
    op.add_column('rental',
        sa.Column('subscription_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_rental_subscription',
        'rental', 'user_subscriptions',
        ['subscription_id'], ['subscription_id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_rental_subscription', 'rental', ['subscription_id'])


def downgrade():
    """
    Rollback subscription system
    """
    # Remove from rental
    op.drop_index('idx_rental_subscription', table_name='rental')
    op.drop_constraint('fk_rental_subscription', 'rental', type_='foreignkey')
    op.drop_column('rental', 'subscription_id')

    # Drop tables in reverse order
    op.drop_index('idx_user_subscriptions_status', table_name='user_subscriptions')
    op.drop_index('idx_user_subscriptions_user', table_name='user_subscriptions')
    op.drop_table('user_subscriptions')

    op.drop_index('idx_subscription_items_package', table_name='subscription_package_items')
    op.drop_table('subscription_package_items')

    op.drop_index('idx_subscription_packages_hub', table_name='subscription_packages')
    op.drop_table('subscription_packages')
