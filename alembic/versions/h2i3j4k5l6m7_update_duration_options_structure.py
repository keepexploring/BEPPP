"""update duration options structure

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2025-12-05 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'h2i3j4k5l6m7'
down_revision = 'g1h2i3j4k5l6'
branch_labels = None
depends_on = None


def upgrade():
    """
    Update duration options structure to properly handle units
    """
    # Rename dropdown_choices to dropdown_options (will store full objects with unit info)
    op.alter_column('cost_structure_duration_options', 'dropdown_choices',
                    new_column_name='dropdown_options',
                    existing_type=sa.Text(),
                    existing_nullable=True)

    # Remove dropdown_labels since we'll store everything in dropdown_options
    op.drop_column('cost_structure_duration_options', 'dropdown_labels')

    # Add custom_unit field for custom input types
    op.add_column('cost_structure_duration_options',
        sa.Column('custom_unit', sa.String(length=20), nullable=True)  # 'days', 'weeks', 'months'
    )


def downgrade():
    """
    Rollback changes
    """
    # Remove custom_unit
    op.drop_column('cost_structure_duration_options', 'custom_unit')

    # Add back dropdown_labels
    op.add_column('cost_structure_duration_options',
        sa.Column('dropdown_labels', sa.Text(), nullable=True)
    )

    # Rename dropdown_options back to dropdown_choices
    op.alter_column('cost_structure_duration_options', 'dropdown_options',
                    new_column_name='dropdown_choices',
                    existing_type=sa.Text(),
                    existing_nullable=True)
