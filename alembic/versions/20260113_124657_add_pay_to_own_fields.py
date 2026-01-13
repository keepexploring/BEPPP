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
    op.add_column('cost_structure', sa.Column('is_pay_to_own', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('cost_structure', sa.Column('item_total_cost', sa.Numeric(10, 2), nullable=True))
    op.add_column('cost_structure', sa.Column('allow_multiple_items', sa.Boolean(), nullable=False, server_default='true'))

    # CostComponent table - Add ownership tracking fields
    op.add_column('cost_component', sa.Column('contributes_to_ownership', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('cost_component', sa.Column('is_percentage_of_remaining', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('cost_component', sa.Column('percentage_value', sa.Numeric(5, 2), nullable=True))

    # PUERental table - Add pay-to-own tracking fields
    op.add_column('pue_rental', sa.Column('is_pay_to_own', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('pue_rental', sa.Column('total_item_cost', sa.Numeric(10, 2), nullable=True))
    op.add_column('pue_rental', sa.Column('total_paid_towards_ownership', sa.Numeric(10, 2), nullable=False, server_default='0.00'))
    op.add_column('pue_rental', sa.Column('total_rental_fees_paid', sa.Numeric(10, 2), nullable=False, server_default='0.00'))
    op.add_column('pue_rental', sa.Column('ownership_percentage', sa.Numeric(5, 2), nullable=False, server_default='0.00'))
    op.add_column('pue_rental', sa.Column('pay_to_own_status', sa.String(20), nullable=True))
    op.add_column('pue_rental', sa.Column('ownership_completion_date', sa.DateTime(), nullable=True))


def downgrade():
    # PUERental table
    op.drop_column('pue_rental', 'ownership_completion_date')
    op.drop_column('pue_rental', 'pay_to_own_status')
    op.drop_column('pue_rental', 'ownership_percentage')
    op.drop_column('pue_rental', 'total_rental_fees_paid')
    op.drop_column('pue_rental', 'total_paid_towards_ownership')
    op.drop_column('pue_rental', 'total_item_cost')
    op.drop_column('pue_rental', 'is_pay_to_own')

    # CostComponent table
    op.drop_column('cost_component', 'percentage_value')
    op.drop_column('cost_component', 'is_percentage_of_remaining')
    op.drop_column('cost_component', 'contributes_to_ownership')

    # CostStructure table
    op.drop_column('cost_structure', 'allow_multiple_items')
    op.drop_column('cost_structure', 'item_total_cost')
    op.drop_column('cost_structure', 'is_pay_to_own')
