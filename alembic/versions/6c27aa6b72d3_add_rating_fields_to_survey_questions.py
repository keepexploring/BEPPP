"""add_rating_fields_to_survey_questions

Revision ID: 6c27aa6b72d3
Revises: 58e95680783f
Create Date: 2026-01-21 14:35:21.035238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c27aa6b72d3'
down_revision: Union[str, Sequence[str], None] = '58e95680783f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add rating-specific fields to return_survey_questions table
    op.add_column('return_survey_questions', sa.Column('rating_min', sa.Integer(), nullable=True))
    op.add_column('return_survey_questions', sa.Column('rating_max', sa.Integer(), nullable=True))
    op.add_column('return_survey_questions', sa.Column('rating_min_label', sa.Text(), nullable=True))
    op.add_column('return_survey_questions', sa.Column('rating_max_label', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove rating fields
    op.drop_column('return_survey_questions', 'rating_max_label')
    op.drop_column('return_survey_questions', 'rating_min_label')
    op.drop_column('return_survey_questions', 'rating_max')
    op.drop_column('return_survey_questions', 'rating_min')
