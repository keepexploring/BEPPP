"""add_notifications_system

Revision ID: c7d8e9f0g1h2
Revises: b1c2d3e4f5g6
Create Date: 2025-12-04 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c7d8e9f0g1h2'
down_revision = 'b1c2d3e4f5g6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add overdue_notification_hours to hub_settings
    op.add_column('hub_settings', sa.Column('overdue_notification_hours', sa.Integer(), server_default='24', nullable=False))

    # Create notifications table
    op.create_table('notifications',
        sa.Column('notification_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hub_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('link_type', sa.String(length=50), nullable=True),
        sa.Column('link_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('notification_id')
    )

    # Create indexes for better query performance
    op.create_index('ix_notifications_hub_id', 'notifications', ['hub_id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_hub_id', table_name='notifications')

    # Drop notifications table
    op.drop_table('notifications')

    # Remove overdue_notification_hours from hub_settings
    op.drop_column('hub_settings', 'overdue_notification_hours')
