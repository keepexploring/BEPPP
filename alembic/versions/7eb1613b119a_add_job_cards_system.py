"""add_job_cards_system

Revision ID: 7eb1613b119a
Revises: 0815ef71fd30
Create Date: 2026-01-22 10:36:27.313351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7eb1613b119a'
down_revision: Union[str, Sequence[str], None] = '0815ef71fd30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create job_cards table
    op.create_table(
        'job_cards',
        sa.Column('card_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('hub_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='todo', nullable=False),
        sa.Column('priority', sa.String(50), server_default='medium', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('assigned_to', sa.BigInteger(), nullable=True),
        sa.Column('linked_entity_type', sa.String(50), nullable=True),
        sa.Column('linked_battery_id', sa.String(50), nullable=True),
        sa.Column('linked_pue_id', sa.String(50), nullable=True),
        sa.Column('linked_user_id', sa.BigInteger(), nullable=True),
        sa.Column('linked_rental_id', sa.BigInteger(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('card_id'),
        sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['user.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['linked_battery_id'], ['bepppbattery.battery_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_pue_id'], ['productiveuseequipment.pue_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_user_id'], ['user.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_rental_id'], ['battery_rentals.rental_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.user_id'], ondelete='SET NULL'),
    )

    # Create indexes for job_cards
    op.create_index('ix_job_cards_hub_id', 'job_cards', ['hub_id'])
    op.create_index('ix_job_cards_status', 'job_cards', ['status'])
    op.create_index('ix_job_cards_assigned_to', 'job_cards', ['assigned_to'])
    op.create_index('ix_job_cards_due_date', 'job_cards', ['due_date'])
    op.create_index('ix_job_cards_linked_battery_id', 'job_cards', ['linked_battery_id'])
    op.create_index('ix_job_cards_linked_pue_id', 'job_cards', ['linked_pue_id'])
    op.create_index('ix_job_cards_linked_user_id', 'job_cards', ['linked_user_id'])
    op.create_index('ix_job_cards_linked_rental_id', 'job_cards', ['linked_rental_id'])

    # Create job_card_activities table
    op.create_table(
        'job_card_activities',
        sa.Column('activity_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('card_id', sa.BigInteger(), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('activity_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('activity_id'),
        sa.ForeignKeyConstraint(['card_id'], ['job_cards.card_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.user_id'], ondelete='SET NULL'),
    )

    # Create indexes for job_card_activities
    op.create_index('ix_job_card_activities_card_id', 'job_card_activities', ['card_id'])
    op.create_index('ix_job_card_activities_created_at', 'job_card_activities', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes for job_card_activities
    op.drop_index('ix_job_card_activities_created_at', table_name='job_card_activities')
    op.drop_index('ix_job_card_activities_card_id', table_name='job_card_activities')

    # Drop job_card_activities table
    op.drop_table('job_card_activities')

    # Drop indexes for job_cards
    op.drop_index('ix_job_cards_linked_rental_id', table_name='job_cards')
    op.drop_index('ix_job_cards_linked_user_id', table_name='job_cards')
    op.drop_index('ix_job_cards_linked_pue_id', table_name='job_cards')
    op.drop_index('ix_job_cards_linked_battery_id', table_name='job_cards')
    op.drop_index('ix_job_cards_due_date', table_name='job_cards')
    op.drop_index('ix_job_cards_assigned_to', table_name='job_cards')
    op.drop_index('ix_job_cards_status', table_name='job_cards')
    op.drop_index('ix_job_cards_hub_id', table_name='job_cards')

    # Drop job_cards table
    op.drop_table('job_cards')
