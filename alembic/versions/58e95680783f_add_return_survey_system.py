"""add_return_survey_system

Revision ID: 58e95680783f
Revises: 4f9da249432b
Create Date: 2026-01-21 13:13:46.664299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58e95680783f'
down_revision: Union[str, Sequence[str], None] = '4f9da249432b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create return_survey_questions table
    op.create_table(
        'return_survey_questions',
        sa.Column('question_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hub_id', sa.BigInteger(), sa.ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(30), nullable=False),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('applies_to_battery', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('applies_to_pue', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('parent_question_id', sa.Integer(), sa.ForeignKey('return_survey_questions.question_id', ondelete='CASCADE'), nullable=True),
        sa.Column('show_if_parent_answer', sa.String(255), nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Create return_survey_question_options table
    op.create_table(
        'return_survey_question_options',
        sa.Column('option_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('return_survey_questions.question_id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_text', sa.String(255), nullable=False),
        sa.Column('option_value', sa.String(100), nullable=False),
        sa.Column('is_open_text_trigger', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Create return_survey_responses table
    op.create_table(
        'return_survey_responses',
        sa.Column('response_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('battery_rental_id', sa.BigInteger(), sa.ForeignKey('battery_rentals.rental_id', ondelete='CASCADE'), nullable=True),
        sa.Column('pue_rental_id', sa.BigInteger(), sa.ForeignKey('puerental.pue_rental_id', ondelete='CASCADE'), nullable=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('return_survey_questions.question_id', ondelete='CASCADE'), nullable=False),
        sa.Column('response_value', sa.Text(), nullable=True),
        sa.Column('response_values', sa.Text(), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('user.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Insert default survey questions based on requirements
    # Question 1: Battery usage
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, sort_order)
        VALUES ('What did you use the battery for during your last rental period?', 'multiple_choice', true, false, true, 1)
    """)

    # Get the question_id for the battery usage question (assuming it's 1)
    op.execute("""
        INSERT INTO return_survey_question_options (question_id, option_text, option_value, is_open_text_trigger, sort_order)
        VALUES
        (1, 'The rented PUE(s) ONLY', 'rented_pue_only', false, 1),
        (1, 'The rented PUE(s) PLUS my own/other devices', 'pue_plus_own', true, 2),
        (1, 'My own/other devices ONLY', 'own_devices_only', true, 3)
    """)

    # Question 2: Conditional - Own devices used (when option 2 or 3 selected)
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, parent_question_id, show_if_parent_answer, sort_order)
        VALUES ('Which own/other devices did you use?', 'multiple_select', true, false, false, 1, '["pue_plus_own", "own_devices_only"]', 2)
    """)

    op.execute("""
        INSERT INTO return_survey_question_options (question_id, option_text, option_value, is_open_text_trigger, sort_order)
        VALUES
        (2, 'Phone charging (self)', 'phone_charging_self', false, 1),
        (2, 'Phone charging (business)', 'phone_charging_business', false, 2),
        (2, 'TV', 'tv', false, 3),
        (2, 'Lamps', 'lamps', false, 4),
        (2, 'Own fridge', 'own_fridge', false, 5),
        (2, 'Own freezer', 'own_freezer', false, 6),
        (2, 'Fan', 'fan', false, 7),
        (2, 'Other (please describe)', 'other', true, 8)
    """)

    # Question 3: PUE services and products
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, sort_order)
        VALUES ('Which services and products delivery did the PUE support in your business during your last rental period?', 'open_text', false, true, false, 3)
    """)

    # Question 4: Satisfaction rating
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, sort_order)
        VALUES ('How satisfied were you with the rental?', 'rating', true, true, true, 4)
    """)

    op.execute("""
        INSERT INTO return_survey_question_options (question_id, option_text, option_value, sort_order)
        VALUES
        (4, 'Super happy', '1', 1),
        (4, 'OK', '2', 2),
        (4, 'Unhappy', '3', 3)
    """)

    # Question 5: Conditional - Reasons for dissatisfaction (when rating is 2 or 3)
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, parent_question_id, show_if_parent_answer, sort_order)
        VALUES ('What disturbed you or could have been better?', 'multiple_select', true, true, false, 4, '["2", "3"]', 5)
    """)

    op.execute("""
        INSERT INTO return_survey_question_options (question_id, option_text, option_value, is_open_text_trigger, sort_order)
        VALUES
        (5, 'Technical challenges', 'technical_challenges', false, 1),
        (5, 'Cost/benefit ratio', 'cost_benefit_ratio', false, 2),
        (5, 'Customer service', 'customer_service', false, 3),
        (5, 'Other (please describe)', 'other', true, 4)
    """)

    # Question 6: Conditional - Technical challenges description (when "technical_challenges" selected in Q5)
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, parent_question_id, show_if_parent_answer, sort_order)
        VALUES ('Please describe the technical challenges you experienced:', 'open_text', true, true, false, 5, '["technical_challenges"]', 6)
    """)

    # Question 7: Would recommend
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, sort_order)
        VALUES ('Would you recommend this service to your family and friends, if more devices would become available?', 'yes_no', true, true, true, 7)
    """)

    op.execute("""
        INSERT INTO return_survey_question_options (question_id, option_text, option_value, sort_order)
        VALUES
        (7, 'Yes', 'yes', 1),
        (7, 'No', 'no', 2)
    """)

    # Question 8: Conditional - Why not recommend (when answer is "no")
    op.execute("""
        INSERT INTO return_survey_questions (question_text, question_type, applies_to_battery, applies_to_pue, is_required, parent_question_id, show_if_parent_answer, sort_order)
        VALUES ('Why would you not recommend this service?', 'open_text', true, true, false, 7, '["no"]', 8)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table('return_survey_responses')
    op.drop_table('return_survey_question_options')
    op.drop_table('return_survey_questions')
