"""convert_battery_pue_ids_to_string

Revision ID: ff7c9c33882f
Revises:
Create Date: 2026-01-16 12:15:04.649168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff7c9c33882f'
down_revision: Union[str, Sequence[str], None] = '4ca3851080c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert battery_id and pue_id from BigInteger to VARCHAR(50) to support alphanumeric IDs."""

    # ========================================================================
    # BATTERY ID MIGRATION
    # ========================================================================

    # 1. Drop foreign key constraints that reference battery_id
    op.drop_constraint('bepppbattery_notes_battery_id_fkey', 'bepppbattery_notes', type_='foreignkey')
    op.drop_constraint('livedata_battery_id_fkey', 'livedata', type_='foreignkey')
    op.drop_constraint('rental_battery_id_fkey', 'rental', type_='foreignkey')
    op.drop_constraint('webhook_logs_battery_id_fkey', 'webhook_logs', type_='foreignkey')
    op.drop_constraint('battery_rental_items_battery_id_fkey', 'battery_rental_items', type_='foreignkey')

    # 2. Add temporary column with new type and copy data
    op.add_column('bepppbattery', sa.Column('battery_id_new', sa.String(50), nullable=True))
    op.execute("UPDATE bepppbattery SET battery_id_new = CAST(battery_id AS VARCHAR(50))")

    # 3. Update foreign key columns to new type and copy data
    op.add_column('bepppbattery_notes', sa.Column('battery_id_new', sa.String(50), nullable=True))
    op.execute("UPDATE bepppbattery_notes SET battery_id_new = CAST(battery_id AS VARCHAR(50))")

    op.add_column('livedata', sa.Column('battery_id_new', sa.String(50), nullable=True))
    op.execute("UPDATE livedata SET battery_id_new = CAST(battery_id AS VARCHAR(50))")

    op.add_column('rental', sa.Column('battery_id_new', sa.String(50), nullable=True))
    op.execute("UPDATE rental SET battery_id_new = CAST(battery_id AS VARCHAR(50))")

    op.add_column('webhook_logs', sa.Column('battery_id_new', sa.String(50), nullable=True))
    op.execute("UPDATE webhook_logs SET battery_id_new = CAST(battery_id AS VARCHAR(50))")

    op.add_column('battery_rental_items', sa.Column('battery_id_new', sa.String(50), nullable=True))
    op.execute("UPDATE battery_rental_items SET battery_id_new = CAST(battery_id AS VARCHAR(50))")

    # 4. Drop old primary key constraint
    op.drop_constraint('bepppbattery_pkey', 'bepppbattery', type_='primary')

    # 5. Drop old columns
    op.drop_column('bepppbattery', 'battery_id')
    op.drop_column('bepppbattery_notes', 'battery_id')
    op.drop_column('livedata', 'battery_id')
    op.drop_column('rental', 'battery_id')
    op.drop_column('webhook_logs', 'battery_id')
    op.drop_column('battery_rental_items', 'battery_id')

    # 6. Rename new columns to original names
    op.alter_column('bepppbattery', 'battery_id_new', new_column_name='battery_id', nullable=False)
    op.alter_column('bepppbattery_notes', 'battery_id_new', new_column_name='battery_id', nullable=False)
    op.alter_column('livedata', 'battery_id_new', new_column_name='battery_id')
    op.alter_column('rental', 'battery_id_new', new_column_name='battery_id')
    op.alter_column('webhook_logs', 'battery_id_new', new_column_name='battery_id')
    op.alter_column('battery_rental_items', 'battery_id_new', new_column_name='battery_id', nullable=False)

    # 7. Recreate primary key constraint
    op.create_primary_key('bepppbattery_pkey', 'bepppbattery', ['battery_id'])

    # 8. Recreate foreign key constraints
    op.create_foreign_key('bepppbattery_notes_battery_id_fkey', 'bepppbattery_notes', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('livedata_battery_id_fkey', 'livedata', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('rental_battery_id_fkey', 'rental', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('webhook_logs_battery_id_fkey', 'webhook_logs', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('battery_rental_items_battery_id_fkey', 'battery_rental_items', 'bepppbattery', ['battery_id'], ['battery_id'], ondelete='CASCADE')

    # ========================================================================
    # PUE ID MIGRATION
    # ========================================================================

    # 1. Drop foreign key constraints that reference pue_id (skip if table doesn't exist)
    try:
        op.drop_constraint('pue_notes_pue_id_fkey', 'pue_notes', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('rental_pue_item_pue_id_fkey', 'rental_pue_item', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('puerental_pue_id_fkey', 'puerental', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('pue_inspections_pue_id_fkey', 'pue_inspections', type_='foreignkey')
    except:
        pass

    # 2. Add temporary column with new type and copy data
    op.add_column('productiveuseequipment', sa.Column('pue_id_new', sa.String(50), nullable=True))
    op.execute("UPDATE productiveuseequipment SET pue_id_new = CAST(pue_id AS VARCHAR(50))")

    # 3. Update foreign key columns to new type and copy data (skip if table doesn't exist)
    try:
        op.add_column('pue_notes', sa.Column('pue_id_new', sa.String(50), nullable=True))
        op.execute("UPDATE pue_notes SET pue_id_new = CAST(pue_id AS VARCHAR(50))")
    except:
        pass

    try:
        op.add_column('rental_pue_item', sa.Column('pue_id_new', sa.String(50), nullable=True))
        op.execute("UPDATE rental_pue_item SET pue_id_new = CAST(pue_id AS VARCHAR(50))")
    except:
        pass

    try:
        op.add_column('puerental', sa.Column('pue_id_new', sa.String(50), nullable=True))
        op.execute("UPDATE puerental SET pue_id_new = CAST(pue_id AS VARCHAR(50))")
    except:
        pass

    try:
        op.add_column('pue_inspections', sa.Column('pue_id_new', sa.String(50), nullable=True))
        op.execute("UPDATE pue_inspections SET pue_id_new = CAST(pue_id AS VARCHAR(50))")
    except:
        pass

    # 4. Drop old primary key constraint
    op.drop_constraint('productiveuseequipment_pkey', 'productiveuseequipment', type_='primary')

    # 5. Drop old columns
    op.drop_column('productiveuseequipment', 'pue_id')
    try:
        op.drop_column('pue_notes', 'pue_id')
    except:
        pass
    try:
        op.drop_column('rental_pue_item', 'pue_id')
    except:
        pass
    try:
        op.drop_column('puerental', 'pue_id')
    except:
        pass
    try:
        op.drop_column('pue_inspections', 'pue_id')
    except:
        pass

    # 6. Rename new columns to original names
    op.alter_column('productiveuseequipment', 'pue_id_new', new_column_name='pue_id', nullable=False)
    try:
        op.alter_column('pue_notes', 'pue_id_new', new_column_name='pue_id', nullable=False)
    except:
        pass
    try:
        op.alter_column('rental_pue_item', 'pue_id_new', new_column_name='pue_id')
    except:
        pass
    try:
        op.alter_column('puerental', 'pue_id_new', new_column_name='pue_id')
    except:
        pass
    try:
        op.alter_column('pue_inspections', 'pue_id_new', new_column_name='pue_id', nullable=False)
    except:
        pass

    # 7. Recreate primary key constraint
    op.create_primary_key('productiveuseequipment_pkey', 'productiveuseequipment', ['pue_id'])

    # 8. Recreate foreign key constraints
    try:
        op.create_foreign_key('pue_notes_pue_id_fkey', 'pue_notes', 'productiveuseequipment', ['pue_id'], ['pue_id'])
    except:
        pass
    try:
        op.create_foreign_key('rental_pue_item_pue_id_fkey', 'rental_pue_item', 'productiveuseequipment', ['pue_id'], ['pue_id'])
    except:
        pass
    try:
        op.create_foreign_key('puerental_pue_id_fkey', 'puerental', 'productiveuseequipment', ['pue_id'], ['pue_id'])
    except:
        pass
    try:
        op.create_foreign_key('pue_inspections_pue_id_fkey', 'pue_inspections', 'productiveuseequipment', ['pue_id'], ['pue_id'], ondelete='CASCADE')
    except:
        pass


def downgrade() -> None:
    """Revert battery_id and pue_id back to BigInteger (only if all IDs are numeric)."""
    # NOTE: This downgrade will fail if any non-numeric IDs have been created
    # It's recommended to not downgrade this migration in production

    # Battery ID downgrade
    op.drop_constraint('bepppbattery_notes_battery_id_fkey', 'bepppbattery_notes', type_='foreignkey')
    op.drop_constraint('livedata_battery_id_fkey', 'livedata', type_='foreignkey')
    op.drop_constraint('rental_battery_id_fkey', 'rental', type_='foreignkey')
    op.drop_constraint('webhook_logs_battery_id_fkey', 'webhook_logs', type_='foreignkey')
    op.drop_constraint('battery_rental_items_battery_id_fkey', 'battery_rental_items', type_='foreignkey')

    op.alter_column('bepppbattery', 'battery_id', type_=sa.BigInteger())
    op.alter_column('bepppbattery_notes', 'battery_id', type_=sa.BigInteger())
    op.alter_column('livedata', 'battery_id', type_=sa.BigInteger())
    op.alter_column('rental', 'battery_id', type_=sa.BigInteger())
    op.alter_column('webhook_logs', 'battery_id', type_=sa.BigInteger())
    op.alter_column('battery_rental_items', 'battery_id', type_=sa.BigInteger())

    op.create_foreign_key('bepppbattery_notes_battery_id_fkey', 'bepppbattery_notes', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('livedata_battery_id_fkey', 'livedata', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('rental_battery_id_fkey', 'rental', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('webhook_logs_battery_id_fkey', 'webhook_logs', 'bepppbattery', ['battery_id'], ['battery_id'])
    op.create_foreign_key('battery_rental_items_battery_id_fkey', 'battery_rental_items', 'bepppbattery', ['battery_id'], ['battery_id'], ondelete='CASCADE')

    # PUE ID downgrade
    try:
        op.drop_constraint('pue_notes_pue_id_fkey', 'pue_notes', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('rental_pue_item_pue_id_fkey', 'rental_pue_item', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('puerental_pue_id_fkey', 'puerental', type_='foreignkey')
    except:
        pass
    try:
        op.drop_constraint('pue_inspections_pue_id_fkey', 'pue_inspections', type_='foreignkey')
    except:
        pass

    op.alter_column('productiveuseequipment', 'pue_id', type_=sa.BigInteger())
    try:
        op.alter_column('pue_notes', 'pue_id', type_=sa.BigInteger())
    except:
        pass
    try:
        op.alter_column('rental_pue_item', 'pue_id', type_=sa.BigInteger())
    except:
        pass
    try:
        op.alter_column('puerental', 'pue_id', type_=sa.BigInteger())
    except:
        pass
    try:
        op.alter_column('pue_inspections', 'pue_id', type_=sa.BigInteger())
    except:
        pass

    try:
        op.create_foreign_key('pue_notes_pue_id_fkey', 'pue_notes', 'productiveuseequipment', ['pue_id'], ['pue_id'])
    except:
        pass
    try:
        op.create_foreign_key('rental_pue_item_pue_id_fkey', 'rental_pue_item', 'productiveuseequipment', ['pue_id'], ['pue_id'])
    except:
        pass
    try:
        op.create_foreign_key('puerental_pue_id_fkey', 'puerental', 'productiveuseequipment', ['pue_id'], ['pue_id'])
    except:
        pass
    try:
        op.create_foreign_key('pue_inspections_pue_id_fkey', 'pue_inspections', 'productiveuseequipment', ['pue_id'], ['pue_id'], ondelete='CASCADE')
    except:
        pass
