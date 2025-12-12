"""add duration options and transaction payment info

Revision ID: g1h2i3j4k5l6
Revises: f0g1h2i3j4k5
Create Date: 2025-12-05 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g1h2i3j4k5l6'
down_revision = 'f0g1h2i3j4k5'
branch_labels = None
depends_on = None


def upgrade():
    """
    This migration adds:
    1. cost_structure_duration_options table - Links duration options to cost structures
    2. payment_type and payment_method columns to account_transactions - Track how payments were made
    """

    # ========================================================================
    # 1. Create cost_structure_duration_options table
    # ========================================================================
    op.create_table(
        'cost_structure_duration_options',
        sa.Column('option_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('structure_id', sa.Integer(), nullable=False),
        sa.Column('input_type', sa.String(length=50), nullable=False),  # 'custom_days', 'custom_weeks', 'custom_months', 'dropdown'
        sa.Column('label', sa.String(length=100), nullable=False),  # Display label e.g., "Number of Days", "Rental Period"
        sa.Column('default_value', sa.Integer(), nullable=True),  # Default value for custom inputs
        sa.Column('min_value', sa.Integer(), nullable=True),  # Minimum value for custom inputs
        sa.Column('max_value', sa.Integer(), nullable=True),  # Maximum value for custom inputs
        sa.Column('dropdown_choices', sa.Text(), nullable=True),  # JSON array of choices e.g., [7, 14, 21, 30]
        sa.Column('dropdown_labels', sa.Text(), nullable=True),  # JSON array of labels e.g., ["1 Week", "2 Weeks", "3 Weeks", "1 Month"]
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('option_id'),
        sa.ForeignKeyConstraint(['structure_id'], ['cost_structures.structure_id'], ondelete='CASCADE')
    )

    # Create index for faster lookups
    op.create_index('idx_duration_options_structure_id', 'cost_structure_duration_options', ['structure_id'])

    # ========================================================================
    # 2. Add payment tracking columns to account_transactions
    # ========================================================================
    op.add_column('account_transactions',
        sa.Column('payment_type', sa.String(length=50), nullable=True)  # 'Cash', 'Mobile Money', 'Bank Transfer', 'Card'
    )
    op.add_column('account_transactions',
        sa.Column('payment_method', sa.String(length=50), nullable=True)  # 'upfront', 'on_return', 'partial', 'deposit_only'
    )

    # Add index for filtering by payment type
    op.create_index('idx_transactions_payment_type', 'account_transactions', ['payment_type'])


def downgrade():
    """
    Rollback changes
    """
    # Remove indexes
    op.drop_index('idx_transactions_payment_type', table_name='account_transactions')
    op.drop_index('idx_duration_options_structure_id', table_name='cost_structure_duration_options')

    # Remove columns from account_transactions
    op.drop_column('account_transactions', 'payment_method')
    op.drop_column('account_transactions', 'payment_type')

    # Drop cost_structure_duration_options table
    op.drop_table('cost_structure_duration_options')
