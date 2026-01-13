"""merge_pay_to_own_and_late_fees

Revision ID: f6bb9eda646a
Revises: 20260113_124657, 8925623423e9
Create Date: 2026-01-13 13:03:03.489696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6bb9eda646a'
down_revision: Union[str, Sequence[str], None] = ('20260113_124657', '8925623423e9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
