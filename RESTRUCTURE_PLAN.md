# BEPPP Rental System Restructure Plan

## Current Status (December 23, 2025)

**Phase 1: Database Changes** ✅ COMPLETE
- All tables created, migration file generated
- Commit: 0cdbe23
- Currently testing with Docker rebuild

**Phase 2: Backend Changes** 🔄 IN PROGRESS
- Models created ✅
- Cost structure estimate API updated ✅
- Remaining: Battery rental endpoints, PUE rental endpoints, inspection endpoints

**Phase 3: Frontend Changes** ⏳ NOT STARTED

**Phase 4: Notifications** ⏳ NOT STARTED

---

## Overview
Major restructure to separate battery rentals from PUE rentals, add pay-to-own functionality for PUE, enhance cost structures, and add inspection tracking.

## Key Changes Summary

1. **Separate Battery and PUE Rentals** - Users can have multiple active battery rentals AND multiple active PUE rentals independently
2. **Pay-to-Own for PUE** - PUE can be rented with pay-to-own option, with separate ledger tracking
3. **Enhanced Cost Structures** - More flexible cost components (per week, per month, recharge fees, etc.)
4. **Battery Rental Enhancements** - Max retention time, overdue handling with combinable options
5. **PUE Inspection System** - Inspection tracking, alerts, and recording

---

## Database Schema Changes

### 1. New/Modified Tables for Battery Rentals

#### `BatteryRental` (NEW - replaces Rental)
```sql
CREATE TABLE battery_rentals (
    rental_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user(user_id),
    hub_id BIGINT REFERENCES solarhub(hub_id),

    -- Rental period
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,  -- Original due date
    actual_return_date TIMESTAMP NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, returned, overdue, cancelled

    -- Cost structure tracking
    cost_structure_id INT REFERENCES cost_structures(structure_id),
    cost_structure_snapshot TEXT,  -- JSON snapshot

    -- Payment tracking
    estimated_cost_before_vat FLOAT,
    estimated_vat FLOAT,
    estimated_cost_total FLOAT,
    final_cost_before_vat FLOAT,
    final_vat FLOAT,
    final_cost_total FLOAT,
    amount_paid FLOAT DEFAULT 0,
    amount_owed FLOAT DEFAULT 0,
    deposit_amount FLOAT DEFAULT 0,
    deposit_returned BOOLEAN DEFAULT FALSE,
    deposit_returned_date TIMESTAMP NULL,
    payment_method VARCHAR(50),
    payment_type VARCHAR(50),
    payment_status VARCHAR(50),

    -- Overdue handling
    max_retention_days INT,  -- From cost structure
    grace_period_days INT NULL,  -- Can be null if no grace period
    grace_period_end_date TIMESTAMP NULL,  -- Calculated
    daily_fine_after_grace FLOAT NULL,  -- Per-day fine after grace
    auto_rollover_enabled BOOLEAN DEFAULT FALSE,  -- Auto extend to next period

    -- Recharge tracking
    max_recharges INT NULL,  -- NULL = unlimited
    recharges_used INT DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by BIGINT REFERENCES user(user_id)
);
```

#### `BatteryRentalItem` (NEW - tracks individual batteries in a rental)
```sql
CREATE TABLE battery_rental_items (
    item_id BIGSERIAL PRIMARY KEY,
    rental_id BIGINT REFERENCES battery_rentals(rental_id) ON DELETE CASCADE,
    battery_id BIGINT REFERENCES bepppbattery(battery_id),

    -- Item-specific tracking
    condition_at_checkout VARCHAR(50),  -- good, fair, damaged
    condition_at_return VARCHAR(50) NULL,
    notes TEXT,

    -- kWh tracking (if cost structure uses kWh)
    kwh_at_checkout FLOAT NULL,
    kwh_at_return FLOAT NULL,
    kwh_used FLOAT NULL,

    added_at TIMESTAMP DEFAULT NOW(),
    returned_at TIMESTAMP NULL
);
```

### 2. Enhanced PUE Rental Tables

#### `PUERental` (MODIFIED - enhanced with pay-to-own)
```sql
ALTER TABLE puerental ADD COLUMN rental_type VARCHAR(20) DEFAULT 'rental';  -- 'rental' or 'pay_to_own'
ALTER TABLE puerental ADD COLUMN pay_to_own_price FLOAT NULL;  -- Total price to own
ALTER TABLE puerental ADD COLUMN cost_structure_id INT REFERENCES cost_structures(structure_id);
ALTER TABLE puerental ADD COLUMN cost_structure_snapshot TEXT;  -- JSON
ALTER TABLE puerental ADD COLUMN payment_status VARCHAR(50) DEFAULT 'active';  -- active, paid_off, defaulted
ALTER TABLE puerental ADD COLUMN next_inspection_date TIMESTAMP NULL;
ALTER TABLE puerental ADD COLUMN inspection_interval_days INT NULL;  -- From PUE settings
ALTER TABLE puerental ADD COLUMN last_inspection_date TIMESTAMP NULL;
```

#### `PUEPayToOwnLedger` (NEW - separate tracking for pay-to-own progress)
```sql
CREATE TABLE pue_pay_to_own_ledger (
    ledger_id BIGSERIAL PRIMARY KEY,
    pue_rental_id BIGINT REFERENCES puerental(pue_rental_id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES user(user_id),

    -- Pay-to-own tracking
    total_price FLOAT NOT NULL,  -- Original price to own
    amount_paid_to_date FLOAT DEFAULT 0,
    amount_remaining FLOAT NOT NULL,
    percent_paid FLOAT GENERATED ALWAYS AS ((amount_paid_to_date / total_price) * 100) STORED,

    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, paid_off, converted_to_rental, defaulted

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `PUEPayToOwnTransaction` (NEW - tracks individual payments toward ownership)
```sql
CREATE TABLE pue_pay_to_own_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    ledger_id BIGINT REFERENCES pue_pay_to_own_ledger(ledger_id) ON DELETE CASCADE,
    account_transaction_id INT REFERENCES account_transactions(transaction_id),  -- Link to main transaction

    amount FLOAT NOT NULL,
    payment_date TIMESTAMP DEFAULT NOW(),
    description TEXT,

    -- Balance tracking
    balance_before FLOAT,
    balance_after FLOAT,

    created_by BIGINT REFERENCES user(user_id)
);
```

#### `PUEInspection` (NEW - inspection tracking)
```sql
CREATE TABLE pue_inspections (
    inspection_id BIGSERIAL PRIMARY KEY,
    pue_id BIGINT REFERENCES productiveuseequipment(pue_id) ON DELETE CASCADE,
    pue_rental_id BIGINT REFERENCES puerental(pue_rental_id) ON DELETE SET NULL,

    inspection_date TIMESTAMP NOT NULL,
    inspector_id BIGINT REFERENCES user(user_id),

    -- Inspection details
    condition VARCHAR(50),  -- excellent, good, fair, poor, damaged
    issues_found TEXT,
    actions_taken TEXT,
    next_inspection_due TIMESTAMP,

    -- Link to notes system (optional - can also just use TEXT fields above)
    note_id BIGINT REFERENCES note(note_id) NULL,

    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Enhanced Cost Structure System

#### `CostComponent` (MODIFIED - add new unit types)
```sql
-- Add new unit_type values:
-- Existing: 'per_day', 'per_hour', 'per_kwh', 'per_kg', 'fixed'
-- New: 'per_week', 'per_month', 'per_recharge', 'one_time'
```

#### `CostStructureMetadata` (NEW - store additional configuration)
```sql
CREATE TABLE cost_structure_metadata (
    metadata_id SERIAL PRIMARY KEY,
    structure_id INT REFERENCES cost_structures(structure_id) ON DELETE CASCADE,

    -- Battery-specific settings
    max_retention_days INT NULL,  -- Max days before must return
    default_grace_period_days INT NULL,
    default_daily_fine FLOAT NULL,
    allow_auto_rollover BOOLEAN DEFAULT FALSE,
    max_recharges INT NULL,  -- NULL = unlimited

    -- PUE-specific settings
    is_pay_to_own_option BOOLEAN DEFAULT FALSE,
    default_pay_to_own_price FLOAT NULL,
    inspection_interval_days INT NULL,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## User Interface Changes

### 1. User Detail Page (`UserDetailsPage.vue`)

**Current:**
- Shows mixed battery + PUE rentals in single table

**New:**
- **Two separate tabs/sections:**
  - "Battery Rentals" - Table showing all battery rentals
  - "PUE Rentals" - Table showing all PUE rentals with pay-to-own progress

**Battery Rentals Section:**
| Rental ID | Start Date | End Date | Batteries | Status | Payment | Actions |
|-----------|------------|----------|-----------|--------|---------|---------|
| #1234 | Jan 1 | Jan 8 | 2x Battery #1, #5 | Active | Paid | View/Return |

**PUE Rentals Section:**
| PUE Item | Type | Start Date | Status | Pay-to-Own Progress | Payment | Actions |
|----------|------|------------|--------|---------------------|---------|---------|
| TV #42 | Pay-to-Own | Dec 1 | Active | 35% (350/1000 MWK) | Current | View/Payment |
| Fan #12 | Rental | Jan 1 | Active | N/A | Current | View/Return |

### 2. Create Rental Pages

**Split into two:**
- `CreateBatteryRentalPage.vue` - Only batteries
- `CreatePUERentalPage.vue` - Only PUE with pay-to-own option

### 3. Settings Page - Cost Structures

**Enhanced cost structure builder:**
- Select item type: Battery Capacity / PUE Type / PUE Item
- Add components:
  - Unit type dropdown: Daily / Weekly / Monthly / Per kWh / Per Recharge / Fixed / One-time
  - Rate input
  - Calculated on return checkbox
- **Battery-specific settings:**
  - Max retention time (days)
  - Grace period (days)
  - Daily fine after grace
  - Auto-rollover option
  - Max recharges (or unlimited)
- **PUE-specific settings:**
  - Available as pay-to-own
  - Default pay-to-own price
  - Inspection interval (days)

### 4. PUE Detail Page

**Add sections:**
- **Current Rental Status**
  - If pay-to-own: Progress bar showing % paid
  - If rental: Regular rental info
- **Inspection Status**
  - Last inspection date
  - Next inspection due
  - Overdue indicator (if applicable)
  - "Record Inspection" button
- **Inspection History**
  - Table of past inspections with dates, inspector, condition

### 5. PUE List Page (Table View)

**Add columns:**
- Inspection Due (with warning icon if overdue)
- Rental Status (Available / Rented / Pay-to-Own)

**Add filters:**
- Inspection overdue
- Rental type (Available / Rental / Pay-to-Own)

### 6. Alerts/Notifications Center

**New alert types:**
- PUE inspection due
- PUE inspection overdue
- Battery retention limit approaching
- Battery overdue (past grace period)

---

## API Endpoint Changes

### Battery Rentals

```
POST   /api/battery-rentals          - Create new battery rental
GET    /api/battery-rentals/{id}     - Get rental details
PUT    /api/battery-rentals/{id}     - Update rental
DELETE /api/battery-rentals/{id}     - Cancel rental
POST   /api/battery-rentals/{id}/return - Return batteries
GET    /api/users/{id}/battery-rentals  - Get user's battery rentals
POST   /api/battery-rentals/{id}/add-battery    - Add battery to existing rental
POST   /api/battery-rentals/{id}/recharge       - Record a recharge
```

### PUE Rentals

```
POST   /api/pue-rentals              - Create new PUE rental (with pay-to-own option)
GET    /api/pue-rentals/{id}         - Get rental details
PUT    /api/pue-rentals/{id}         - Update rental
DELETE /api/pue-rentals/{id}         - Cancel/return rental
GET    /api/users/{id}/pue-rentals   - Get user's PUE rentals
POST   /api/pue-rentals/{id}/payment - Record payment (applies to pay-to-own if applicable)
POST   /api/pue-rentals/{id}/convert-to-rental  - Convert pay-to-own back to rental
GET    /api/pue-rentals/{id}/pay-to-own-ledger  - Get pay-to-own progress
```

### PUE Inspections

```
POST   /api/pue/{id}/inspections     - Record inspection
GET    /api/pue/{id}/inspections     - Get inspection history
GET    /api/inspections/due           - Get all PUE due for inspection
GET    /api/inspections/overdue       - Get all overdue inspections
```

### Cost Structures (Enhanced)

```
POST   /api/cost-structures          - Create (with new metadata)
PUT    /api/cost-structures/{id}     - Update (with metadata)
GET    /api/cost-structures/{id}/calculate - Calculate cost with overdue handling
```

---

## Migration Strategy

### Phase 1: Database Changes ✅ COMPLETE
1. ✅ Create new tables (BatteryRental, BatteryRentalItem, PUEPayToOwnLedger, etc.)
2. ✅ Add new columns to existing tables
3. ✅ **DELETE existing rental data** (as per user decision)
4. ✅ Update indexes
5. ✅ Created migration file: `alembic/versions/f177f72b3403_restructure_rental_system.py`
6. ✅ Committed: 0cdbe23 "Add database migration and models for rental system restructure"
7. 🔄 Testing migration locally (Docker rebuild in progress)

### Phase 2: Backend Changes (IN PROGRESS)
1. ✅ Create new models in `models.py`
   - ✅ BatteryRental
   - ✅ BatteryRentalItem
   - ✅ CostStructureBatteryConfig
   - ✅ CostStructurePUEConfig
   - ✅ PUEPayToOwnLedger
   - ✅ PUEPayToOwnTransaction
   - ✅ PUEInspection
2. ⏳ Update API endpoints in `main.py`
   - ✅ Update cost structure estimate API with new unit types (per_week, per_month, per_recharge, one_time)
   - ⏳ Update return cost calculation with overdue logic
   - ⏳ Create battery rental endpoints
   - ⏳ Create PUE rental endpoints
   - ⏳ Create inspection endpoints
3. ⏳ Add business logic for:
   - ⏳ Overdue calculation with grace periods
   - ⏳ Pay-to-own payment allocation
   - ⏳ Inspection due date calculation
   - ⏳ Recharge limit tracking

### Phase 3: Frontend Changes (NOT STARTED)
1. ⏳ Update user detail page with separate sections
2. ⏳ Create new rental creation pages
3. ⏳ Update settings page with enhanced cost structure builder
4. ⏳ Add inspection recording UI
5. ⏳ Update PUE list/detail pages

### Phase 4: Notifications (NOT STARTED)
1. ⏳ Add inspection due alerts
2. ⏳ Add overdue rental alerts
3. ⏳ Add retention limit warnings

---

## Business Logic Details

### 1. Battery Overdue Handling (Combinable)

Example: 7-day rental, 2-day grace, then 500 MWK/day fine

```
Day 1-7:   Normal rental period
Day 8-9:   Grace period (no charge)
Day 10+:   Daily fine of 500 MWK/day
```

Configuration in cost structure:
- `max_retention_days`: 7
- `grace_period_days`: 2
- `daily_fine_after_grace`: 500
- `auto_rollover_enabled`: false

### 2. Pay-to-Own Workflow

**Creating PUE Rental with Pay-to-Own:**
1. Select PUE item
2. Choose cost structure with pay-to-own enabled
3. Set pay-to-own price (e.g., 50,000 MWK)
4. Create rental + create PUEPayToOwnLedger entry

**Making Payments:**
1. User makes payment (via existing payment system)
2. Payment is recorded in AccountTransaction
3. If PUE has active pay-to-own, create PUEPayToOwnTransaction
4. Update PUEPayToOwnLedger amounts
5. When amount_remaining = 0, mark as 'paid_off' and transfer ownership

**Converting Back to Rental:**
1. Hub admin clicks "Convert to Rental"
2. System shows: "User has paid 15,000 MWK toward 50,000 MWK (30%)"
3. Options:
   - Refund percentage (e.g., 80% = 12,000 MWK refund)
   - Apply to rental cost (all 15,000 MWK counts as rental payments)
   - Hybrid (partial refund, rest to rental)
4. Create transactions accordingly
5. Update PUEPayToOwnLedger status to 'converted_to_rental'

### 3. Inspection System

**Automatic Scheduling:**
- When PUE rental created with inspection interval (e.g., 30 days)
- Set `next_inspection_date` = start_date + 30 days
- Daily job checks for inspections due in next 7 days → create alert
- Daily job checks for overdue inspections → create alert

**Recording Inspection:**
1. Navigate to PUE detail page (or from inspections due list)
2. Click "Record Inspection"
3. Fill form: date, condition, issues, actions
4. Option to create linked note
5. System calculates next inspection date
6. Alert is cleared

---

## Technical Notes

### Migration File Naming
```
alembic/versions/XXXXXXXX_restructure_rental_system.py
```

### JSON Snapshots for Cost Structures
Store complete cost structure config at time of rental:
```json
{
  "structure_id": 123,
  "name": "Standard 7-day Battery",
  "components": [
    {"name": "Daily Rate", "unit_type": "per_day", "rate": 500},
    {"name": "Recharge Fee", "unit_type": "per_recharge", "rate": 200}
  ],
  "metadata": {
    "max_retention_days": 7,
    "grace_period_days": 2,
    "daily_fine_after_grace": 500,
    "max_recharges": 2
  }
}
```

### Notes Category for Inspections
Add new note category: `inspection`
Can be used for detailed inspection notes with photos/attachments

---

## Next Steps

1. Review and approve this plan
2. Create database migration
3. Update models.py
4. Implement backend API endpoints
5. Update frontend components
6. Test migration and functionality
7. Deploy to production

---

## Questions for Clarification

1. ✅ Should existing rentals be migrated? **Answer: Delete existing data**
2. ✅ Can overdue options be combined? **Answer: Yes**
3. ✅ Can users rent multiple batteries at once? **Answer: Yes**
4. ✅ How should pay-to-own payments work? **Answer: Separate ledger**

5. When converting pay-to-own back to rental, should the refund percentage be configurable per-transaction, or should there be a default?
6. Should inspections be mandatory (block rentals if overdue) or just advisory?
7. For battery max retention, should this be a hard block (can't extend past it) or just trigger alerts?
