"""add_id_document_photo_to_users

Revision ID: e9a53be3515c
Revises: 1889b584bb38
Create Date: 2026-01-16 17:14:42.033193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9a53be3515c'
down_revision: Union[str, Sequence[str], None] = '1889b584bb38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user', sa.Column('id_document_photo_url', sa.String(500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'id_document_photo_url')
