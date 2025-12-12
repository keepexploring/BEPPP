"""add_payment_status_fields_to_rental

Revision ID: 682a95137536
Revises: k7l8m9n0o1p2
Create Date: 2025-12-09 11:39:28.258435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '682a95137536'
down_revision: Union[str, Sequence[str], None] = 'k7l8m9n0o1p2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add payment status tracking fields to rental table if they don't exist
    from sqlalchemy import inspect
    from alembic import context

    conn = context.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('rental')]

    if 'payment_status' not in columns:
        op.add_column('rental', sa.Column('payment_status', sa.String(50), nullable=True))
    if 'amount_paid' not in columns:
        op.add_column('rental', sa.Column('amount_paid', sa.Float(), nullable=True, server_default='0'))
    if 'amount_owed' not in columns:
        op.add_column('rental', sa.Column('amount_owed', sa.Float(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove payment status tracking fields from rental table
    op.drop_column('rental', 'amount_owed')
    op.drop_column('rental', 'amount_paid')
    op.drop_column('rental', 'payment_status')
