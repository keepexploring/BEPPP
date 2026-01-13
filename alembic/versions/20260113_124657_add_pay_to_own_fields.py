"""Add pay-to-own fields

Revision ID: 20260113_124657
Revises: f177f72b3403
Create Date: 2026-01-13 12:46:57

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260113_124657'
down_revision = 'f177f72b3403'
branch_labels = None
depends_on = None


def upgrade():
    # CostStructure table - Add pay-to-own fields
    op.add_column('cost_structures', sa.Column('is_pay_to_own', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('cost_structures', sa.Column('item_total_cost', sa.Numeric(10, 2), nullable=True))
    op.add_column('cost_structures', sa.Column('allow_multiple_items', sa.Boolean(), nullable=False, server_default='true'))

    # CostComponent table - Add ownership tracking fields
    op.add_column('cost_components', sa.Column('contributes_to_ownership', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('cost_components', sa.Column('is_percentage_of_remaining', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('cost_components', sa.Column('percentage_value', sa.Numeric(5, 2), nullable=True))

    # PUERental table - Add pay-to-own tracking fields
    op.add_column('puerental', sa.Column('is_pay_to_own', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('puerental', sa.Column('total_item_cost', sa.Numeric(10, 2), nullable=True))
    op.add_column('puerental', sa.Column('total_paid_towards_ownership', sa.Numeric(10, 2), nullable=False, server_default='0.00'))
    op.add_column('puerental', sa.Column('total_rental_fees_paid', sa.Numeric(10, 2), nullable=False, server_default='0.00'))
    op.add_column('puerental', sa.Column('ownership_percentage', sa.Numeric(5, 2), nullable=False, server_default='0.00'))
    op.add_column('puerental', sa.Column('pay_to_own_status', sa.String(20), nullable=True))
    op.add_column('puerental', sa.Column('ownership_completion_date', sa.DateTime(), nullable=True))


def downgrade():
    # PUERental table
    op.drop_column('puerental', 'ownership_completion_date')
    op.drop_column('puerental', 'pay_to_own_status')
    op.drop_column('puerental', 'ownership_percentage')
    op.drop_column('puerental', 'total_rental_fees_paid')
    op.drop_column('puerental', 'total_paid_towards_ownership')
    op.drop_column('puerental', 'total_item_cost')
    op.drop_column('puerental', 'is_pay_to_own')

    # CostComponent table
    op.drop_column('cost_components', 'percentage_value')
    op.drop_column('cost_components', 'is_percentage_of_remaining')
    op.drop_column('cost_components', 'contributes_to_ownership')

    # CostStructure table
    op.drop_column('cost_structures', 'allow_multiple_items')
    op.drop_column('cost_structures', 'item_total_cost')
    op.drop_column('cost_structures', 'is_pay_to_own')
