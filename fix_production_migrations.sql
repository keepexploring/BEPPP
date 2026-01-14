-- One-time script to fix production database migration state
-- This adds any missing columns/tables and stamps alembic to correct version

BEGIN;

-- Add cost_structure_id to puerental if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'puerental' AND column_name = 'cost_structure_id'
    ) THEN
        ALTER TABLE puerental ADD COLUMN cost_structure_id INTEGER;
        ALTER TABLE puerental ADD CONSTRAINT fk_puerental_cost_structure
            FOREIGN KEY (cost_structure_id) REFERENCES cost_structures(structure_id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add short_id to productiveuseequipment if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'productiveuseequipment' AND column_name = 'short_id'
    ) THEN
        ALTER TABLE productiveuseequipment ADD COLUMN short_id VARCHAR(20);
    END IF;
END $$;

-- Create pue_inspections table if it doesn't exist
CREATE TABLE IF NOT EXISTS pue_inspections (
    inspection_id SERIAL PRIMARY KEY,
    pue_id INTEGER NOT NULL REFERENCES productiveuseequipment(pue_id) ON DELETE CASCADE,
    pue_rental_id INTEGER REFERENCES puerental(pue_rental_id) ON DELETE SET NULL,
    inspection_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    inspector_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    condition VARCHAR(50) NOT NULL,
    issues_found TEXT,
    actions_taken TEXT,
    next_inspection_due TIMESTAMP WITH TIME ZONE,
    note_id INTEGER REFERENCES pue_notes(note_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add recurring payment fields to puerental if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'puerental' AND column_name = 'has_recurring_payment'
    ) THEN
        ALTER TABLE puerental ADD COLUMN has_recurring_payment BOOLEAN NOT NULL DEFAULT false;
        ALTER TABLE puerental ADD COLUMN recurring_payment_frequency VARCHAR(50);
        ALTER TABLE puerental ADD COLUMN next_payment_due_date TIMESTAMP WITH TIME ZONE;
        ALTER TABLE puerental ADD COLUMN last_payment_date TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Add recurring payment fields to cost_components if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'cost_components' AND column_name = 'is_recurring_payment'
    ) THEN
        ALTER TABLE cost_components ADD COLUMN is_recurring_payment BOOLEAN NOT NULL DEFAULT false;
        ALTER TABLE cost_components ADD COLUMN recurring_interval NUMERIC(5,2);
    END IF;
END $$;

-- Set alembic version to the latest (after all our changes)
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('d30fceecdec1');

COMMIT;

-- Verify what we created
\dt pue_inspections
\d puerental
\d productiveuseequipment
SELECT * FROM alembic_version;
