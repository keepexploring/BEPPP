"""restructure_rental_system

Revision ID: f177f72b3403
Revises: 3ff9feb8478f
Create Date: 2025-12-23 15:29:53.119580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f177f72b3403'
down_revision: Union[str, Sequence[str], None] = '3ff9feb8478f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for rental system restructure."""

    # =============================================================================
    # STEP 1: Delete existing rental data (as agreed by user)
    # =============================================================================
    op.execute('DELETE FROM rental_notes')
    op.execute('DELETE FROM rental_pue_item')
    op.execute('DELETE FROM puerental_notes')
    op.execute('DELETE FROM puerental')
    op.execute('DELETE FROM rental')

    # =============================================================================
    # STEP 2: Create cost_structure_battery_config table
    # =============================================================================
    op.create_table(
        'cost_structure_battery_config',
        sa.Column('config_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('structure_id', sa.Integer(), nullable=False),

        # Rental period settings
        sa.Column('max_retention_days', sa.Integer(), nullable=True),
        sa.Column('allow_extensions', sa.Boolean(), server_default='true', nullable=False),

        # Overdue handling (combinable options)
        sa.Column('grace_period_days', sa.Integer(), nullable=True),
        sa.Column('daily_fine_after_grace', sa.Float(), nullable=True),
        sa.Column('auto_rollover_to_next_period', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('rollover_discount_percentage', sa.Float(), nullable=True),

        # Recharge settings
        sa.Column('max_recharges', sa.Integer(), nullable=True),
        sa.Column('recharge_fee_per_occurrence', sa.Float(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.PrimaryKeyConstraint('config_id'),
        sa.ForeignKeyConstraint(['structure_id'], ['cost_structures.structure_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('structure_id')  # One config per cost structure
    )

    # =============================================================================
    # STEP 3: Create cost_structure_pue_config table
    # =============================================================================
    op.create_table(
        'cost_structure_pue_config',
        sa.Column('config_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('structure_id', sa.Integer(), nullable=False),

        # Pay-to-own settings
        sa.Column('supports_pay_to_own', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('default_pay_to_own_price', sa.Float(), nullable=True),
        sa.Column('pay_to_own_conversion_formula', sa.String(50), nullable=True),  # 'fixed_price', 'cumulative_rental', 'percentage_based'

        # Inspection settings
        sa.Column('requires_inspections', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('inspection_interval_days', sa.Integer(), nullable=True),
        sa.Column('inspection_reminder_days', sa.Integer(), server_default='7', nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.PrimaryKeyConstraint('config_id'),
        sa.ForeignKeyConstraint(['structure_id'], ['cost_structures.structure_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('structure_id')
    )

    # =============================================================================
    # STEP 4: Create battery_rentals table (NEW - separate from PUE rentals)
    # =============================================================================
    op.create_table(
        'battery_rentals',
        sa.Column('rental_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('hub_id', sa.BigInteger(), nullable=False),

        # Rental period
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),  # Original due date
        sa.Column('actual_return_date', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('status', sa.String(20), server_default='active', nullable=False),  # active, returned, overdue, cancelled

        # Cost structure tracking
        sa.Column('cost_structure_id', sa.Integer(), nullable=True),
        sa.Column('cost_structure_snapshot', sa.Text(), nullable=True),  # JSON snapshot

        # Payment tracking
        sa.Column('estimated_cost_before_vat', sa.Float(), nullable=True),
        sa.Column('estimated_vat', sa.Float(), nullable=True),
        sa.Column('estimated_cost_total', sa.Float(), nullable=True),
        sa.Column('final_cost_before_vat', sa.Float(), nullable=True),
        sa.Column('final_vat', sa.Float(), nullable=True),
        sa.Column('final_cost_total', sa.Float(), nullable=True),
        sa.Column('amount_paid', sa.Float(), server_default='0', nullable=False),
        sa.Column('amount_owed', sa.Float(), server_default='0', nullable=False),
        sa.Column('deposit_amount', sa.Float(), server_default='0', nullable=False),
        sa.Column('deposit_returned', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deposit_returned_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_type', sa.String(50), nullable=True),
        sa.Column('payment_status', sa.String(50), nullable=True),

        # Overdue handling
        sa.Column('max_retention_days', sa.Integer(), nullable=True),  # From cost structure
        sa.Column('grace_period_days', sa.Integer(), nullable=True),
        sa.Column('grace_period_end_date', sa.DateTime(timezone=True), nullable=True),  # Calculated
        sa.Column('daily_fine_after_grace', sa.Float(), nullable=True),
        sa.Column('auto_rollover_enabled', sa.Boolean(), server_default='false', nullable=False),

        # Recharge tracking
        sa.Column('max_recharges', sa.Integer(), nullable=True),  # NULL = unlimited
        sa.Column('recharges_used', sa.Integer(), server_default='0', nullable=False),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),

        sa.PrimaryKeyConstraint('rental_id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cost_structure_id'], ['cost_structures.structure_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['user.user_id'], ondelete='SET NULL')
    )

    # Create index for common queries
    op.create_index('ix_battery_rentals_user_id', 'battery_rentals', ['user_id'])
    op.create_index('ix_battery_rentals_hub_id', 'battery_rentals', ['hub_id'])
    op.create_index('ix_battery_rentals_status', 'battery_rentals', ['status'])

    # =============================================================================
    # STEP 5: Create battery_rental_items table (tracks individual batteries in rental)
    # =============================================================================
    op.create_table(
        'battery_rental_items',
        sa.Column('item_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('rental_id', sa.BigInteger(), nullable=False),
        sa.Column('battery_id', sa.BigInteger(), nullable=False),

        # Item-specific tracking
        sa.Column('condition_at_checkout', sa.String(50), nullable=True),  # good, fair, damaged
        sa.Column('condition_at_return', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # kWh tracking (if cost structure uses kWh)
        sa.Column('kwh_at_checkout', sa.Float(), nullable=True),
        sa.Column('kwh_at_return', sa.Float(), nullable=True),
        sa.Column('kwh_used', sa.Float(), nullable=True),

        # Timestamps
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('item_id'),
        sa.ForeignKeyConstraint(['rental_id'], ['battery_rentals.rental_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['battery_id'], ['bepppbattery.battery_id'], ondelete='CASCADE')
    )

    op.create_index('ix_battery_rental_items_rental_id', 'battery_rental_items', ['rental_id'])
    op.create_index('ix_battery_rental_items_battery_id', 'battery_rental_items', ['battery_id'])

    # =============================================================================
    # STEP 6: Create battery_rental_notes junction table
    # =============================================================================
    op.create_table(
        'battery_rental_notes',
        sa.Column('rental_id', sa.BigInteger(), nullable=False),
        sa.Column('note_id', sa.BigInteger(), nullable=False),

        sa.PrimaryKeyConstraint('rental_id', 'note_id'),
        sa.ForeignKeyConstraint(['rental_id'], ['battery_rentals.rental_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['note_id'], ['note.id'], ondelete='CASCADE')
    )

    # =============================================================================
    # STEP 7: Modify PUERental table - add pay-to-own and inspection columns
    # =============================================================================
    op.add_column('puerental', sa.Column('rental_type', sa.String(20), server_default='rental', nullable=False))
    op.add_column('puerental', sa.Column('pay_to_own_price', sa.Float(), nullable=True))
    op.add_column('puerental', sa.Column('cost_structure_id', sa.Integer(), nullable=True))
    op.add_column('puerental', sa.Column('cost_structure_snapshot', sa.Text(), nullable=True))
    op.add_column('puerental', sa.Column('payment_status', sa.String(50), server_default='active', nullable=False))
    op.add_column('puerental', sa.Column('next_inspection_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('puerental', sa.Column('inspection_interval_days', sa.Integer(), nullable=True))
    op.add_column('puerental', sa.Column('last_inspection_date', sa.DateTime(timezone=True), nullable=True))

    # Add foreign key for cost_structure_id
    op.create_foreign_key(
        'fk_puerental_cost_structure',
        'puerental', 'cost_structures',
        ['cost_structure_id'], ['structure_id'],
        ondelete='SET NULL'
    )

    # =============================================================================
    # STEP 8: Create pue_pay_to_own_ledger table
    # =============================================================================
    op.create_table(
        'pue_pay_to_own_ledger',
        sa.Column('ledger_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pue_rental_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),

        # Pay-to-own tracking
        sa.Column('total_price', sa.Float(), nullable=False),  # Original price to own
        sa.Column('amount_paid_to_date', sa.Float(), server_default='0', nullable=False),
        sa.Column('amount_remaining', sa.Float(), nullable=False),
        # percent_paid calculated as GENERATED column

        # Status
        sa.Column('status', sa.String(20), server_default='active', nullable=False),  # active, paid_off, converted_to_rental, defaulted

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.PrimaryKeyConstraint('ledger_id'),
        sa.ForeignKeyConstraint(['pue_rental_id'], ['puerental.pue_rental_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ondelete='CASCADE')
    )

    op.create_index('ix_pue_pay_to_own_ledger_rental_id', 'pue_pay_to_own_ledger', ['pue_rental_id'])
    op.create_index('ix_pue_pay_to_own_ledger_user_id', 'pue_pay_to_own_ledger', ['user_id'])

    # =============================================================================
    # STEP 9: Create pue_pay_to_own_transactions table
    # =============================================================================
    op.create_table(
        'pue_pay_to_own_transactions',
        sa.Column('transaction_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ledger_id', sa.BigInteger(), nullable=False),
        sa.Column('account_transaction_id', sa.Integer(), nullable=True),  # Link to main transaction

        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Balance tracking
        sa.Column('balance_before', sa.Float(), nullable=True),
        sa.Column('balance_after', sa.Float(), nullable=True),

        sa.Column('created_by', sa.BigInteger(), nullable=True),

        sa.PrimaryKeyConstraint('transaction_id'),
        sa.ForeignKeyConstraint(['ledger_id'], ['pue_pay_to_own_ledger.ledger_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_transaction_id'], ['account_transactions.transaction_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['user.user_id'], ondelete='SET NULL')
    )

    # =============================================================================
    # STEP 10: Create pue_inspections table
    # =============================================================================
    op.create_table(
        'pue_inspections',
        sa.Column('inspection_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pue_id', sa.BigInteger(), nullable=False),
        sa.Column('pue_rental_id', sa.BigInteger(), nullable=True),  # Optional link to rental

        sa.Column('inspection_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('inspector_id', sa.BigInteger(), nullable=True),

        # Inspection details
        sa.Column('condition', sa.String(50), nullable=True),  # excellent, good, fair, poor, damaged
        sa.Column('issues_found', sa.Text(), nullable=True),
        sa.Column('actions_taken', sa.Text(), nullable=True),
        sa.Column('next_inspection_due', sa.DateTime(timezone=True), nullable=True),

        # Optional link to notes system
        sa.Column('note_id', sa.BigInteger(), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        sa.PrimaryKeyConstraint('inspection_id'),
        sa.ForeignKeyConstraint(['pue_id'], ['productiveuseequipment.pue_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pue_rental_id'], ['puerental.pue_rental_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inspector_id'], ['user.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['note_id'], ['note.id'], ondelete='SET NULL')
    )

    op.create_index('ix_pue_inspections_pue_id', 'pue_inspections', ['pue_id'])
    op.create_index('ix_pue_inspections_inspection_date', 'pue_inspections', ['inspection_date'])

    # =============================================================================
    # STEP 11: Add pay_to_own_default_refund_percentage to hub_settings
    # =============================================================================
    op.add_column('hub_settings', sa.Column('pay_to_own_default_refund_percentage', sa.Float(), server_default='80.0', nullable=False))


def downgrade() -> None:
    """Downgrade schema - reverse all changes."""

    # Remove new column from hub_settings
    op.drop_column('hub_settings', 'pay_to_own_default_refund_percentage')

    # Drop new tables
    op.drop_index('ix_pue_inspections_inspection_date', 'pue_inspections')
    op.drop_index('ix_pue_inspections_pue_id', 'pue_inspections')
    op.drop_table('pue_inspections')

    op.drop_table('pue_pay_to_own_transactions')

    op.drop_index('ix_pue_pay_to_own_ledger_user_id', 'pue_pay_to_own_ledger')
    op.drop_index('ix_pue_pay_to_own_ledger_rental_id', 'pue_pay_to_own_ledger')
    op.drop_table('pue_pay_to_own_ledger')

    # Remove new columns from puerental
    op.drop_constraint('fk_puerental_cost_structure', 'puerental', type_='foreignkey')
    op.drop_column('puerental', 'last_inspection_date')
    op.drop_column('puerental', 'inspection_interval_days')
    op.drop_column('puerental', 'next_inspection_date')
    op.drop_column('puerental', 'payment_status')
    op.drop_column('puerental', 'cost_structure_snapshot')
    op.drop_column('puerental', 'cost_structure_id')
    op.drop_column('puerental', 'pay_to_own_price')
    op.drop_column('puerental', 'rental_type')

    # Drop battery rental tables
    op.drop_table('battery_rental_notes')

    op.drop_index('ix_battery_rental_items_battery_id', 'battery_rental_items')
    op.drop_index('ix_battery_rental_items_rental_id', 'battery_rental_items')
    op.drop_table('battery_rental_items')

    op.drop_index('ix_battery_rentals_status', 'battery_rentals')
    op.drop_index('ix_battery_rentals_hub_id', 'battery_rentals')
    op.drop_index('ix_battery_rentals_user_id', 'battery_rentals')
    op.drop_table('battery_rentals')

    # Drop cost structure config tables
    op.drop_table('cost_structure_pue_config')
    op.drop_table('cost_structure_battery_config')
