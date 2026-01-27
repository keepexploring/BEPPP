"""add_enhanced_customer_fields_and_settings

Revision ID: 4f9da249432b
Revises: e9a53be3515c
Create Date: 2026-01-21 11:52:09.844103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f9da249432b'
down_revision: Union[str, Sequence[str], None] = 'e9a53be3515c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new name fields to user table
    op.add_column('user', sa.Column('first_names', sa.String(255), nullable=True))
    op.add_column('user', sa.Column('last_name', sa.String(255), nullable=True))

    # Add new address field (renamed from address)
    op.add_column('user', sa.Column('physical_address', sa.String(), nullable=True))

    # Add new customer demographic fields
    op.add_column('user', sa.Column('date_of_birth', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('gesi_status', sa.String(100), nullable=True))
    op.add_column('user', sa.Column('business_category', sa.String(100), nullable=True))
    op.add_column('user', sa.Column('monthly_energy_expenditure', sa.Float(), nullable=True))
    op.add_column('user', sa.Column('main_reason_for_signup', sa.String(100), nullable=True))

    # Create customer_field_options table for configurable dropdown options
    op.create_table(
        'customer_field_options',
        sa.Column('option_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hub_id', sa.BigInteger(), sa.ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True),
        sa.Column('field_name', sa.String(50), nullable=False),
        sa.Column('option_value', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Insert some default GESI status options
    op.execute("""
        INSERT INTO customer_field_options (field_name, option_value, description, sort_order) VALUES
        ('gesi_status', 'Youth (<18)', 'Young person under 18 years old', 1),
        ('gesi_status', 'Adult (18-55)', 'Adult between 18 and 55 years old', 2),
        ('gesi_status', 'Older (>55)', 'Person over 55 years old', 3),
        ('gesi_status', 'Person with Disability', 'Person with disability', 4),
        ('gesi_status', 'Female-headed Household', 'Female-headed household', 5)
    """)

    # Insert some default business category options
    op.execute("""
        INSERT INTO customer_field_options (field_name, option_value, description, sort_order) VALUES
        ('business_category', 'No Business', 'Not using for business purposes', 1),
        ('business_category', 'Micro Business', 'Very small business (1-2 people)', 2),
        ('business_category', 'Small Business', 'Small business (3-10 people)', 3),
        ('business_category', 'Medium Business', 'Medium business (11-50 people)', 4),
        ('business_category', 'Large Business', 'Large business (50+ people)', 5)
    """)

    # Insert some default signup reason options
    op.execute("""
        INSERT INTO customer_field_options (field_name, option_value, description, sort_order) VALUES
        ('main_reason_for_signup', 'Reduce Energy Costs', 'To reduce spending on energy', 1),
        ('main_reason_for_signup', 'Reliable Power Supply', 'For consistent access to electricity', 2),
        ('main_reason_for_signup', 'Business Operations', 'To run business equipment', 3),
        ('main_reason_for_signup', 'Home Use', 'For household electricity needs', 4),
        ('main_reason_for_signup', 'Environmental Reasons', 'To use clean/renewable energy', 5),
        ('main_reason_for_signup', 'No Grid Access', 'No access to national grid', 6)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop customer_field_options table
    op.drop_table('customer_field_options')

    # Remove new columns from user table
    op.drop_column('user', 'main_reason_for_signup')
    op.drop_column('user', 'monthly_energy_expenditure')
    op.drop_column('user', 'business_category')
    op.drop_column('user', 'gesi_status')
    op.drop_column('user', 'date_of_birth')
    op.drop_column('user', 'physical_address')
    op.drop_column('user', 'last_name')
    op.drop_column('user', 'first_names')
