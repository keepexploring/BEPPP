"""add_energy_split_decimal_durations_deposit_holds

Revision ID: a1b2c3d4e5f6
Revises: c4e5f6a78b90
Create Date: 2026-03-11 12:00:00.000000

Changes:
1. Add monthly_energy_electricity and monthly_energy_heat columns to user table
2. ALTER duration option columns from Integer to Float for decimal support
3. CREATE deposit_holds table for credit hold system
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c4e5f6a78b90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add energy split columns to user table
    op.add_column('user', sa.Column('monthly_energy_electricity', sa.Float(), nullable=True))
    op.add_column('user', sa.Column('monthly_energy_heat', sa.Float(), nullable=True))

    # 2. ALTER duration option columns from Integer to Float
    # PostgreSQL supports ALTER COLUMN TYPE directly
    op.alter_column('cost_structure_duration_options', 'default_value',
                     existing_type=sa.Integer(),
                     type_=sa.Float(),
                     existing_nullable=True)
    op.alter_column('cost_structure_duration_options', 'min_value',
                     existing_type=sa.Integer(),
                     type_=sa.Float(),
                     existing_nullable=True)
    op.alter_column('cost_structure_duration_options', 'max_value',
                     existing_type=sa.Integer(),
                     type_=sa.Float(),
                     existing_nullable=True)

    # 3. CREATE deposit_holds table
    op.create_table('deposit_holds',
        sa.Column('hold_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('rental_id', sa.BigInteger(), nullable=True),
        sa.Column('pue_rental_id', sa.BigInteger(), nullable=True),
        sa.Column('rental_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='held', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['user_accounts.account_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('hold_id')
    )


def downgrade() -> None:
    # Drop deposit_holds table
    op.drop_table('deposit_holds')

    # Revert duration option columns back to Integer
    op.alter_column('cost_structure_duration_options', 'max_value',
                     existing_type=sa.Float(),
                     type_=sa.Integer(),
                     existing_nullable=True)
    op.alter_column('cost_structure_duration_options', 'min_value',
                     existing_type=sa.Float(),
                     type_=sa.Integer(),
                     existing_nullable=True)
    op.alter_column('cost_structure_duration_options', 'default_value',
                     existing_type=sa.Float(),
                     type_=sa.Integer(),
                     existing_nullable=True)

    # Remove energy split columns
    op.drop_column('user', 'monthly_energy_heat')
    op.drop_column('user', 'monthly_energy_electricity')
