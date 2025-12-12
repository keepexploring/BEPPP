"""add deposit to cost structures

Revision ID: k7l8m9n0o1p2
Revises: h3i4j5k6l7m8
Create Date: 2025-12-08 15:39:20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k7l8m9n0o1p2'
down_revision = 'h3i4j5k6l7m8'
branch_labels = None
depends_on = None


def upgrade():
    # Add deposit_amount column to cost_structures table
    op.add_column('cost_structures', sa.Column('deposit_amount', sa.Float(), server_default='0', nullable=False))


def downgrade():
    # Remove deposit_amount column from cost_structures table
    op.drop_column('cost_structures', 'deposit_amount')
