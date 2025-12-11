"""add_cost_structure_system

Revision ID: f0g1h2i3j4k5
Revises: e9f0g1h2i3j4
Create Date: 2025-12-04 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f0g1h2i3j4k5'
down_revision = 'e9f0g1h2i3j4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cost_structures table
    op.create_table('cost_structures',
        sa.Column('structure_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hub_id', sa.BigInteger(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('item_reference', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('structure_id')
    )
    op.create_index('ix_cost_structures_hub_id', 'cost_structures', ['hub_id'])
    op.create_index('ix_cost_structures_item', 'cost_structures', ['item_type', 'item_reference'])

    # Create cost_components table
    op.create_table('cost_components',
        sa.Column('component_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('structure_id', sa.Integer(), nullable=False),
        sa.Column('component_name', sa.String(length=100), nullable=False),
        sa.Column('unit_type', sa.String(length=50), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('is_calculated_on_return', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['structure_id'], ['cost_structures.structure_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('component_id')
    )
    op.create_index('ix_cost_components_structure_id', 'cost_components', ['structure_id'])

    # Add cost structure tracking fields to rental table
    op.add_column('rental', sa.Column('cost_structure_id', sa.Integer(), nullable=True))
    op.add_column('rental', sa.Column('cost_structure_snapshot', sa.Text(), nullable=True))
    op.add_column('rental', sa.Column('estimated_cost_before_vat', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('estimated_vat', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('estimated_cost_total', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('final_cost_before_vat', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('final_vat', sa.Float(), nullable=True))
    op.add_column('rental', sa.Column('final_cost_total', sa.Float(), nullable=True))

    # Add VAT and timezone to hub_settings
    op.add_column('hub_settings', sa.Column('vat_percentage', sa.Float(), server_default='0.00', nullable=False))
    op.add_column('hub_settings', sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False))


def downgrade() -> None:
    # Remove fields from hub_settings
    op.drop_column('hub_settings', 'timezone')
    op.drop_column('hub_settings', 'vat_percentage')

    # Remove fields from rental table
    op.drop_column('rental', 'final_cost_total')
    op.drop_column('rental', 'final_vat')
    op.drop_column('rental', 'final_cost_before_vat')
    op.drop_column('rental', 'estimated_cost_total')
    op.drop_column('rental', 'estimated_vat')
    op.drop_column('rental', 'estimated_cost_before_vat')
    op.drop_column('rental', 'cost_structure_snapshot')
    op.drop_column('rental', 'cost_structure_id')

    # Drop cost_components table
    op.drop_index('ix_cost_components_structure_id', table_name='cost_components')
    op.drop_table('cost_components')

    # Drop cost_structures table
    op.drop_index('ix_cost_structures_item', table_name='cost_structures')
    op.drop_index('ix_cost_structures_hub_id', table_name='cost_structures')
    op.drop_table('cost_structures')
