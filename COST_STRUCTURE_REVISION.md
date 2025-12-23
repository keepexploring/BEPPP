# Cost Structure System - Complete Revision

## Current State Analysis

### Existing Unit Types (in database)
- `per_day` ✅
- `per_hour` ✅
- `per_kwh` ✅
- `per_kg` ✅
- `fixed` ✅

### Existing Calculation Logic
**Estimate Function** (`/settings/cost-structures/{id}/estimate`):
- Supports: per_day, per_hour, per_kwh, per_kg, fixed
- Missing: per_week, per_month (even though return calc has them!)

**Return Cost Calculation** (`/rentals/{id}/calculate-return-cost`):
- Supports: per_day, per_hour, per_week ✅, per_month ✅, per_kwh, fixed
- Already has per_week and per_month implemented!

### Missing Functionality
1. ❌ `per_week` unit type (in DB and estimate function)
2. ❌ `per_month` unit type (in DB and estimate function)
3. ❌ `per_recharge` unit type for battery recharges
4. ❌ `one_time` unit type for one-off fees
5. ❌ Battery rental metadata (max retention, grace periods, fines, recharge limits)
6. ❌ PUE rental metadata (pay-to-own pricing, inspection intervals)
7. ❌ Overdue cost calculation logic
8. ❌ Recharge counting and limits
9. ❌ Pay-to-own progress tracking

---

## Required Changes

### 1. Database Schema Changes

#### A. Update `CostComponent` unit types
```sql
-- Add new ENUM values or update CHECK constraint
-- New values: 'per_week', 'per_month', 'per_recharge', 'one_time'
```

#### B. Create `cost_structure_battery_config` table
```sql
CREATE TABLE cost_structure_battery_config (
    config_id SERIAL PRIMARY KEY,
    structure_id INT REFERENCES cost_structures(structure_id) ON DELETE CASCADE UNIQUE,

    -- Rental period settings
    max_retention_days INT NULL,  -- Max days before MUST return (soft limit)
    allow_extensions BOOLEAN DEFAULT TRUE,

    -- Overdue handling (combinable options)
    grace_period_days INT NULL,  -- Days of grace before penalties
    daily_fine_after_grace FLOAT NULL,  -- Per-day fine after grace
    auto_rollover_to_next_period BOOLEAN DEFAULT FALSE,  -- Auto-extend to next rental period
    rollover_discount_percentage FLOAT NULL,  -- Discount on auto-rollover (e.g., 10%)

    -- Recharge settings
    max_recharges INT NULL,  -- NULL = unlimited
    recharge_fee_per_occurrence FLOAT NULL,  -- Fee per recharge (if per_recharge component not used)

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### C. Create `cost_structure_pue_config` table
```sql
CREATE TABLE cost_structure_pue_config (
    config_id SERIAL PRIMARY KEY,
    structure_id INT REFERENCES cost_structures(structure_id) ON DELETE CASCADE UNIQUE,

    -- Pay-to-own settings
    supports_pay_to_own BOOLEAN DEFAULT FALSE,
    default_pay_to_own_price FLOAT NULL,  -- Default price to own
    pay_to_own_conversion_formula VARCHAR(50) NULL,  -- 'fixed_price', 'cumulative_rental', 'percentage_based'

    -- Inspection settings
    requires_inspections BOOLEAN DEFAULT FALSE,
    inspection_interval_days INT NULL,  -- Days between required inspections
    inspection_reminder_days INT DEFAULT 7,  -- Days before inspection to send reminder

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### D. Add `default_refund_percentage` to HubSettings
```sql
ALTER TABLE hub_settings ADD COLUMN pay_to_own_default_refund_percentage FLOAT DEFAULT 80.0;
```

---

### 2. Updated Cost Calculation Logic

#### A. Estimate Function Updates

**Add missing unit types:**

```python
# In estimate_rental_cost function

elif comp.unit_type == 'per_week':
    if duration_unit == 'weeks':
        quantity = duration_value
    elif duration_unit == 'days':
        quantity = duration_value / 7
    elif duration_unit == 'months':
        quantity = duration_value * 4.33  # Approximate weeks per month
    elif duration_unit == 'hours':
        quantity = duration_value / (24 * 7)
    amount = quantity * comp.rate

elif comp.unit_type == 'per_month':
    if duration_unit == 'months':
        quantity = duration_value
    elif duration_unit == 'weeks':
        quantity = duration_value / 4.33
    elif duration_unit == 'days':
        quantity = duration_value / 30
    elif duration_unit == 'hours':
        quantity = duration_value / (24 * 30)
    amount = quantity * comp.rate

elif comp.unit_type == 'per_recharge':
    # Estimate based on expected recharges
    expected_recharges = request.get('expected_recharges', 0)
    quantity = expected_recharges
    amount = quantity * comp.rate

elif comp.unit_type == 'one_time':
    # One-time fee charged once regardless of duration
    quantity = 1
    amount = comp.rate
```

**Add battery config handling:**

```python
# Get battery-specific config if this is a battery rental
battery_config = None
if structure.item_type == 'battery_capacity':
    battery_config = db.query(CostStructureBatteryConfig).filter(
        CostStructureBatteryConfig.structure_id == structure_id
    ).first()

# Include battery config in response
response = {
    "structure_id": structure.structure_id,
    "structure_name": structure.name,
    "breakdown": breakdown,
    "subtotal": float(subtotal),
    "vat_percentage": float(vat_percentage),
    "vat_amount": float(vat_amount),
    "total": float(total),
    "deposit_amount": float(structure.deposit_amount or 0),
    "has_estimated_component": has_estimated_component
}

if battery_config:
    response["battery_config"] = {
        "max_retention_days": battery_config.max_retention_days,
        "grace_period_days": battery_config.grace_period_days,
        "daily_fine_after_grace": float(battery_config.daily_fine_after_grace or 0),
        "max_recharges": battery_config.max_recharges
    }
```

#### B. Return Cost Calculation Updates

**Add per_recharge handling:**

```python
elif component.unit_type == 'per_recharge':
    # Get actual recharge count from rental
    recharges_used = getattr(rental, 'recharges_used', 0) or 0
    quantity = recharges_used
    component_cost = component.rate * recharges_used
```

**Add one_time handling:**

```python
elif component.unit_type == 'one_time':
    # One-time fee charged once
    quantity = 1
    component_cost = component.rate
```

**Add overdue calculation logic:**

```python
# After calculating base costs, check for overdue penalties
overdue_days = 0
overdue_charges = 0
grace_period_used = 0

if rental.max_retention_days and actual_days > rental.max_retention_days:
    # Rental is overdue
    overdue_days = actual_days - rental.max_retention_days

    # Check grace period
    if rental.grace_period_days and rental.grace_period_days > 0:
        if overdue_days <= rental.grace_period_days:
            # Still in grace period
            grace_period_used = overdue_days
            overdue_days = 0
        else:
            # Past grace period
            grace_period_used = rental.grace_period_days
            overdue_days = overdue_days - rental.grace_period_days

    # Calculate daily fines
    if overdue_days > 0 and rental.daily_fine_after_grace:
        overdue_charges = overdue_days * rental.daily_fine_after_grace

        cost_breakdown.append({
            "component_name": "Late Return Fine",
            "unit_type": "per_day",
            "rate": float(rental.daily_fine_after_grace),
            "quantity": float(overdue_days),
            "amount": float(overdue_charges)
        })

        subtotal += overdue_charges

# Add overdue info to response
return {
    # ... existing fields ...
    "overdue_info": {
        "max_retention_days": rental.max_retention_days,
        "actual_days": round(actual_days, 2),
        "overdue_days": round(overdue_days, 2) if overdue_days > 0 else 0,
        "grace_period_days": rental.grace_period_days,
        "grace_period_used": round(grace_period_used, 2),
        "daily_fine_rate": float(rental.daily_fine_after_grace or 0),
        "overdue_charges": float(overdue_charges)
    }
}
```

**Add recharge limit checking:**

```python
# After calculating costs
recharge_info = {
    "max_recharges": rental.max_recharges,
    "recharges_used": rental.recharges_used or 0,
    "recharges_remaining": None,
    "limit_exceeded": False
}

if rental.max_recharges is not None:
    recharges_remaining = rental.max_recharges - (rental.recharges_used or 0)
    recharge_info["recharges_remaining"] = max(0, recharges_remaining)
    recharge_info["limit_exceeded"] = (rental.recharges_used or 0) > rental.max_recharges

# Include in response
response["recharge_info"] = recharge_info
```

---

### 3. New Cost Structure Builder UI (Settings Page)

#### A. Enhanced Form Fields

**Item Type Selection:**
```
[ ] Battery Capacity
[ ] PUE Type
[ ] PUE Item
```

**Cost Components Section:**
```
Components:
┌─────────────────────────────────────────────────┐
│ Component 1:                                     │
│   Name: [Daily Rental Fee              ]        │
│   Unit Type: [Per Day ▼]                        │
│   Rate: [500] MWK                                │
│   ☐ Calculate on return                         │
│   [Remove]                                       │
├─────────────────────────────────────────────────┤
│ Component 2:                                     │
│   Name: [Recharge Fee               ]           │
│   Unit Type: [Per Recharge ▼]                   │
│   Rate: [200] MWK                                │
│   ☐ Calculate on return                         │
│   [Remove]                                       │
└─────────────────────────────────────────────────┘
[+ Add Component]

Unit Type Options:
- Per Hour
- Per Day
- Per Week
- Per Month
- Per kWh
- Per Recharge (batteries only)
- Fixed (one per rental)
- One-Time (charged once)
```

**Battery-Specific Settings** (shown when item_type = battery_capacity):
```
┌─────────────────────────────────────────────────┐
│ Battery Rental Settings                          │
├─────────────────────────────────────────────────┤
│ Max Retention Time: [7] days                     │
│ ☑ Allow extensions                              │
│                                                   │
│ Overdue Handling:                                │
│   Grace Period: [2] days (0 = no grace)         │
│   Daily Fine After Grace: [500] MWK              │
│   ☐ Auto-rollover to next period                │
│   Rollover Discount: [10] %                      │
│                                                   │
│ Recharge Settings:                               │
│   Max Recharges: [2] (leave empty for unlimited)│
└─────────────────────────────────────────────────┘
```

**PUE-Specific Settings** (shown when item_type = pue_type or pue_item):
```
┌─────────────────────────────────────────────────┐
│ PUE Rental Settings                              │
├─────────────────────────────────────────────────┤
│ Pay-to-Own:                                      │
│   ☑ Available as pay-to-own                     │
│   Default Price: [50000] MWK                     │
│                                                   │
│ Inspection Settings:                             │
│   ☑ Requires inspections                        │
│   Inspection Interval: [30] days                 │
│   Reminder Before: [7] days                      │
└─────────────────────────────────────────────────┘
```

---

### 4. Rental Creation Page Updates

#### A. Battery Rental Creation

**Step 1: Select Batteries**
- Select one or more batteries
- Show capacity, status, current charge

**Step 2: Select Cost Structure**
- Show available cost structures for battery capacity
- Display cost breakdown preview
- Show max retention, grace period, recharge limits

**Step 3: Set Rental Period**
- Start date
- Expected return date (with warning if exceeds max retention)
- Show cost estimate with components breakdown

**Step 4: Payment & Deposit**
- Show total estimated cost
- Choose payment method
- Collect deposit
- Set payment timing (upfront/on-return/partial)

**Display Warnings:**
```
⚠️ Max Retention: 7 days
   After 7 days, a 2-day grace period applies
   Then 500 MWK/day late fee

ℹ️  Recharge Limit: 2 recharges included
   Additional recharges: 200 MWK each
```

#### B. PUE Rental Creation

**Step 1: Select PUE**
- Select PUE item
- Show current status, last inspection date

**Step 2: Rental Type**
```
( ) Regular Rental
( ) Pay-to-Own

[If Pay-to-Own selected:]
  Pay-to-Own Price: [50000] MWK
  Rental payments will count toward ownership
```

**Step 3: Select Cost Structure**
- Show available cost structures for PUE type
- Display cost breakdown

**Step 4: Rental Period** (if regular rental)
- Start date
- Expected return date
- Cost estimate

**Step 5: Payment**
- Show total/initial cost
- Payment method
- For pay-to-own: Show first payment amount

**Display Info:**
```
ℹ️  Inspection Due: Jan 15, 2024 (in 28 days)
```

---

### 5. Return Processing Updates

#### A. Battery Return

**Enhanced Return Form:**
```
Battery Return - Rental #1234
─────────────────────────────
Batteries:
  [x] Battery #5
  [x] Battery #12

Return Date: [2024-01-15] (Today ▼)

Actual Days: 9 days (7 day rental + 2 grace days)
Status: ⚠️ In Grace Period

kWh Used:
  Battery #5: [12.5] kWh
  Battery #12: [10.2] kWh

Recharges Used: [2] (limit: 2)

─────────────────────────────
COST BREAKDOWN:

Base Rental:
  Daily Fee (9 days × 500 MWK): 4,500 MWK

Usage:
  kWh Charge (22.7 kWh × 50 MWK): 1,135 MWK
  Recharge Fees (2 × 200 MWK): 400 MWK

Subtotal: 6,035 MWK
VAT (15%): 905 MWK
Total: 6,940 MWK

Amount Paid: 3,000 MWK
Amount Due: 3,940 MWK

[Process Return]
```

**If Past Grace Period:**
```
Status: 🔴 OVERDUE

Actual Days: 11 days
  Rental Period: 7 days
  Grace Period: 2 days
  Overdue: 2 days

Late Fees:
  Daily Fine (2 days × 500 MWK): 1,000 MWK

Total with Late Fees: 7,940 MWK
```

#### B. PUE Return

**Regular Rental:**
- Similar to battery return
- Record final condition
- Schedule next inspection (if re-renting)

**Pay-to-Own Return (Early Termination):**
```
Return Pay-to-Own PUE - TV #42
───────────────────────────────
Current Progress:
  Total Price: 50,000 MWK
  Amount Paid: 15,000 MWK
  Remaining: 35,000 MWK
  Progress: 30% ███░░░░░░░

Return Options:
( ) Refund percentage of payments
    Refund: [80]% = 12,000 MWK refund

( ) Apply all to rental costs
    All 15,000 MWK counts as rental payments

( ) Hybrid
    Refund: [50]% = 7,500 MWK
    Apply to rental: 7,500 MWK

Reason for return:
[____________________________________________]

[Process Return]
```

---

### 6. API Endpoint Changes

#### New Endpoints

```
POST   /api/cost-structures                         - Create with battery/PUE config
PUT    /api/cost-structures/{id}                    - Update with battery/PUE config
GET    /api/cost-structures/{id}/full               - Get with all config details

POST   /api/battery-rentals/{id}/record-recharge    - Record a recharge
GET    /api/battery-rentals/{id}/calculate-overdue  - Calculate overdue charges

POST   /api/pue-rentals/{id}/pay-to-own-payment     - Record payment toward ownership
GET    /api/pue-rentals/{id}/pay-to-own-progress    - Get ownership progress
POST   /api/pue-rentals/{id}/convert-to-rental      - Convert pay-to-own to rental
```

#### Updated Endpoints

```
POST   /api/settings/cost-structures/{id}/estimate
  - Add support for per_week, per_month, per_recharge, one_time
  - Include battery/PUE config in response
  - Add expected_recharges parameter

GET    /api/rentals/{id}/calculate-return-cost
  - Add overdue calculation logic
  - Add recharge limit checking
  - Return overdue_info and recharge_info
```

---

### 7. Migration Steps

#### Phase 1: Database
1. Add new unit type constraints
2. Create cost_structure_battery_config table
3. Create cost_structure_pue_config table
4. Add pay_to_own_default_refund_percentage to hub_settings

#### Phase 2: Backend
1. Update models.py with new tables
2. Update estimate function with new unit types
3. Update return cost function with overdue logic
4. Create new endpoints for recharge recording, pay-to-own

#### Phase 3: Frontend
1. Update SettingsPage cost structure builder
2. Update rental creation pages
3. Update return processing forms
4. Add pay-to-own conversion UI

---

### 8. Testing Scenarios

#### Battery Rental Scenarios

**Scenario 1: On-time return**
- 7-day rental, returned on day 7
- 2 recharges used (limit: 2)
- Expected: Base costs only, no penalties

**Scenario 2: Grace period return**
- 7-day rental, returned on day 9
- Within grace period (2 days)
- Expected: Extended base costs, no fines

**Scenario 3: Late return with fines**
- 7-day rental, returned on day 12
- Grace period: 2 days, overdue: 3 days
- Expected: Base costs + (3 × daily fine)

**Scenario 4: Recharge limit exceeded**
- Max 2 recharges, used 3
- Expected: Additional recharge fee charged

#### PUE Rental Scenarios

**Scenario 5: Pay-to-own completion**
- 50,000 MWK price, paid in full
- Expected: Ownership transferred, status = 'paid_off'

**Scenario 6: Pay-to-own conversion to rental**
- 30% paid (15,000 MWK of 50,000 MWK)
- 80% refund policy
- Expected: 12,000 MWK refunded, 3,000 MWK to rental costs

---

## Summary of Changes

### Database Tables
- ✅ Add unit types: per_week, per_month, per_recharge, one_time
- ✅ New table: cost_structure_battery_config
- ✅ New table: cost_structure_pue_config
- ✅ Update hub_settings: pay_to_own_default_refund_percentage

### Backend Logic
- ✅ Update estimate function: add per_week, per_month, per_recharge, one_time
- ✅ Update return cost function: add per_recharge, one_time, overdue logic
- ✅ New logic: recharge counting and limits
- ✅ New logic: pay-to-own progress tracking

### Frontend Changes
- ✅ Settings: Enhanced cost structure builder with battery/PUE config
- ✅ Rental creation: Cost estimate preview with warnings
- ✅ Return processing: Overdue calculation, refund options
- ✅ Pay-to-own: Progress display, conversion workflow

### API Endpoints
- ✅ Enhanced: POST /cost-structures (with config)
- ✅ Enhanced: POST /cost-structures/{id}/estimate
- ✅ Enhanced: GET /rentals/{id}/calculate-return-cost
- ✅ New: POST /battery-rentals/{id}/record-recharge
- ✅ New: POST /pue-rentals/{id}/pay-to-own-payment
- ✅ New: POST /pue-rentals/{id}/convert-to-rental
