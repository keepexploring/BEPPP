"""add cost_structure_id to puerental

Revision ID: 20260114_add_cost_structure_id
Revises: d30fceecdec1
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260114_add_cost_structure_id'
down_revision = 'd30fceecdec1'
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL with IF NOT EXISTS to make this idempotent
    op.execute("""
        DO $$
        BEGIN
            -- Add column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'puerental' AND column_name = 'cost_structure_id'
            ) THEN
                ALTER TABLE puerental ADD COLUMN cost_structure_id INTEGER;
            END IF;

            -- Add foreign key if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'puerental' AND constraint_name = 'fk_puerental_cost_structure'
            ) THEN
                ALTER TABLE puerental
                ADD CONSTRAINT fk_puerental_cost_structure
                FOREIGN KEY (cost_structure_id)
                REFERENCES cost_structures(structure_id)
                ON DELETE SET NULL;
            END IF;
        END
        $$;
    """)


def downgrade():
    # Remove foreign key constraint if exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'puerental' AND constraint_name = 'fk_puerental_cost_structure'
            ) THEN
                ALTER TABLE puerental DROP CONSTRAINT fk_puerental_cost_structure;
            END IF;
        END
        $$;
    """)

    # Remove column if exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'puerental' AND column_name = 'cost_structure_id'
            ) THEN
                ALTER TABLE puerental DROP COLUMN cost_structure_id;
            END IF;
        END
        $$;
    """)
