"""add_payment_types

Revision ID: e9f0g1h2i3j4
Revises: d8e9f0g1h2i3
Create Date: 2025-12-04 16:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e9f0g1h2i3j4'
down_revision = 'd8e9f0g1h2i3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_types table
    op.create_table('payment_types',
        sa.Column('type_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hub_id', sa.BigInteger(), nullable=True),
        sa.Column('type_name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hub_id'], ['solarhub.hub_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('type_id')
    )

    # Create indexes for better query performance
    op.create_index('ix_payment_types_hub_id', 'payment_types', ['hub_id'])
    op.create_index('ix_payment_types_name', 'payment_types', ['type_name'])

    # Add payment_type field to rental table
    op.add_column('rental', sa.Column('payment_type', sa.String(length=50), nullable=True))

    # Insert default payment types (global)
    op.execute("""
        INSERT INTO payment_types (type_name, description, sort_order, hub_id)
        VALUES
            ('Cash', 'Cash payment', 1, NULL),
            ('Mobile Money', 'Mobile money transfer (e.g. M-Pesa)', 2, NULL),
            ('Bank Transfer', 'Direct bank transfer', 3, NULL),
            ('Credit/Debit Card', 'Card payment', 4, NULL)
    """)


def downgrade() -> None:
    # Remove payment_type field from rental table
    op.drop_column('rental', 'payment_type')

    # Drop indexes
    op.drop_index('ix_payment_types_name', table_name='payment_types')
    op.drop_index('ix_payment_types_hub_id', table_name='payment_types')

    # Drop payment_types table
    op.drop_table('payment_types')
