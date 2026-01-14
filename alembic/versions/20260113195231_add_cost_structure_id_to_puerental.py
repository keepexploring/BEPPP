"""add cost_structure_id to puerental

Revision ID: 20260113195231
Revises: 
Create Date: 2026-01-13T19:52:31.272242

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260113195231'
down_revision = 'd30fceecdec1'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column exists before adding
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='puerental' AND column_name='cost_structure_id'
    """))
    column_exists = result.fetchone() is not None

    if not column_exists:
        # Add cost_structure_id column to puerental table
        op.add_column('puerental',
            sa.Column('cost_structure_id', sa.Integer(), nullable=True)
        )

    # Check if foreign key exists before adding
    result = conn.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name='puerental' AND constraint_name='fk_puerental_cost_structure'
    """))
    fk_exists = result.fetchone() is not None

    if not fk_exists:
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_puerental_cost_structure',
            'puerental', 'cost_structures',
            ['cost_structure_id'], ['structure_id'],
            ondelete='SET NULL'
        )


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_puerental_cost_structure', 'puerental', type_='foreignkey')

    # Remove column
    op.drop_column('puerental', 'cost_structure_id')
