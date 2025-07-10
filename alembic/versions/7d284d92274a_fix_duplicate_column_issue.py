"""Fix duplicate column issue

Revision ID: 7d284d92274a
Revises: 50ecca511334
Create Date: 2025-07-10 15:23:53.645794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d284d92274a'
down_revision: Union[str, Sequence[str], None] = '50ecca511334'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column exists before adding to avoid duplicate column error
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('rental')]
    
    if 'battery_returned' not in columns:
        op.add_column('rental', sa.Column('battery_returned', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    pass
