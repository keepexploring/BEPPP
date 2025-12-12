"""add double entry accounting

Revision ID: h3i4j5k6l7m8
Revises:
Create Date: 2025-12-08 15:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'h3i4j5k6l7m8'
down_revision = ('i3j4k5l6m7n8',)  # Merge from existing head
branch_labels = None
depends_on = None


def upgrade():
    # Create ledger_entries table
    op.create_table(
        'ledger_entries',
        sa.Column('entry_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False),
        sa.Column('debit', sa.Float(), nullable=True),
        sa.Column('credit', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['account_transactions.transaction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('entry_id')
    )

    # Create account_reconciliations table
    op.create_table(
        'account_reconciliations',
        sa.Column('reconciliation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('expected_balance', sa.Float(), nullable=False),
        sa.Column('actual_balance', sa.Float(), nullable=False),
        sa.Column('difference', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.BigInteger(), nullable=True),
        sa.Column('reconciliation_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['user_accounts.account_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['user.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('reconciliation_id')
    )

    # Create indexes for better query performance
    op.create_index('idx_ledger_transaction_id', 'ledger_entries', ['transaction_id'])
    op.create_index('idx_ledger_account_type', 'ledger_entries', ['account_type'])
    op.create_index('idx_ledger_account_name', 'ledger_entries', ['account_name'])
    op.create_index('idx_reconciliation_account_id', 'account_reconciliations', ['account_id'])
    op.create_index('idx_reconciliation_status', 'account_reconciliations', ['status'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_reconciliation_status', table_name='account_reconciliations')
    op.drop_index('idx_reconciliation_account_id', table_name='account_reconciliations')
    op.drop_index('idx_ledger_account_name', table_name='ledger_entries')
    op.drop_index('idx_ledger_account_type', table_name='ledger_entries')
    op.drop_index('idx_ledger_transaction_id', table_name='ledger_entries')

    # Drop tables
    op.drop_table('account_reconciliations')
    op.drop_table('ledger_entries')
