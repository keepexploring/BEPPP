"""add short_id to users and batteries for QR codes

Revision ID: a2f3e4d5c6b7
Revises: 0c9a1f2202d4
Create Date: 2025-11-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2f3e4d5c6b7'
down_revision: Union[str, Sequence[str], None] = '0c9a1f2202d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add short_id to user table
    op.add_column('user', sa.Column('short_id', sa.String(length=20), nullable=True))
    op.create_index('ix_user_short_id', 'user', ['short_id'], unique=True)

    # Add short_id to bepppbattery table
    op.add_column('bepppbattery', sa.Column('short_id', sa.String(length=20), nullable=True))
    op.create_index('ix_bepppbattery_short_id', 'bepppbattery', ['short_id'], unique=True)

    # Backfill existing users with generated short_ids
    connection = op.get_bind()

    # Get all existing users
    users = connection.execute(sa.text("SELECT user_id FROM \"user\" ORDER BY user_id")).fetchall()
    for user in users:
        user_id = user[0]
        short_id = f"BH-{str(user_id).zfill(4)}"
        connection.execute(
            sa.text("UPDATE \"user\" SET short_id = :short_id WHERE user_id = :user_id"),
            {"short_id": short_id, "user_id": user_id}
        )

    # Get all existing batteries
    batteries = connection.execute(sa.text("SELECT battery_id FROM bepppbattery ORDER BY battery_id")).fetchall()
    for battery in batteries:
        battery_id = battery[0]
        short_id = f"BAT-{str(battery_id).zfill(4)}"
        connection.execute(
            sa.text("UPDATE bepppbattery SET short_id = :short_id WHERE battery_id = :battery_id"),
            {"short_id": short_id, "battery_id": battery_id}
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('ix_bepppbattery_short_id', table_name='bepppbattery')
    op.drop_index('ix_user_short_id', table_name='user')

    # Drop columns
    op.drop_column('bepppbattery', 'short_id')
    op.drop_column('user', 'short_id')
