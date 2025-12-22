"""add_user_id_autoincrement

Revision ID: 0fdba945efbc
Revises: afb93f5d0e87
Create Date: 2025-12-22 14:42:10.987988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fdba945efbc'
down_revision: Union[str, Sequence[str], None] = 'afb93f5d0e87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add auto-increment sequence to user.user_id column."""
    # Create sequence for user_id
    op.execute('CREATE SEQUENCE IF NOT EXISTS user_user_id_seq OWNED BY "user".user_id')

    # Set sequence to current max user_id value
    op.execute('SELECT setval(\'user_user_id_seq\', (SELECT COALESCE(MAX(user_id), 0) FROM "user"), true)')

    # Set sequence as default for user_id column
    op.execute('ALTER TABLE "user" ALTER COLUMN user_id SET DEFAULT nextval(\'user_user_id_seq\')')


def downgrade() -> None:
    """Remove auto-increment sequence from user.user_id column."""
    # Remove default from column
    op.execute('ALTER TABLE "user" ALTER COLUMN user_id DROP DEFAULT')

    # Drop sequence
    op.execute('DROP SEQUENCE IF EXISTS user_user_id_seq')
