# Changelog - May 2026

## Summary

Features and fixes implemented in May 2026: battery recharge workflow, auto-return on charge detection, stale-cache fix for rental form dropdowns, user report builder, and telemetry chart improvements.

---

## Battery Recharge Workflow

### Overview

Cost structures for battery rentals now support a **per-recharge billing model** alongside the standard per-day rate. This is designed for hubs where customers bring batteries back to be recharged at the hub and then take them out again, rather than renting a fresh battery each time.

### How it works

1. **Configure the cost structure** in Settings → Cost Structures:
   - Set `Max Recharges` (e.g. 2) to limit how many recharge cycles are allowed per rental
   - Add a `Per Recharge` cost component with the flat fee charged each time the battery is recharged
   - Optionally set `Count initial checkout as recharge` if the first collection should count as recharge #1

2. **Creating a rental** works identically — select the cost structure as normal.

3. **When a customer returns the battery to be recharged** (within the rental period):
   - Open the return dialog for their active rental
   - A green **"Recharge instead of returning?"** banner appears at the top (only when recharges remain and the rental period has not expired)
   - Click **Record Recharge** — this increments the recharge counter and keeps the rental active
   - The customer takes the battery back out; the rental continues

4. **When the customer makes their final return**:
   - The standard return dialog is used
   - Final cost is calculated as: `(daily rate × days used) + (recharge fee × recharges used)`

### Conditions for the recharge banner to appear

| Condition | Why |
|-----------|-----|
| Battery rental (not PUE) | Recharge is only applicable to battery rentals |
| Rental status is `active` | Cannot recharge an already-returned rental |
| Cost structure has `max_recharges` set | Must be a recharge-type cost structure |
| `recharges_used < max_recharges` | All recharge slots have not been used up |
| Current date ≤ rental end date | Recharge is not offered if the rental period has already expired |

If any condition fails, only the normal "Confirm Return" button is shown.

### Backend

- **Endpoint**: `POST /battery-rentals/{rental_id}/recharge`
- **Body**: `{ battery_id, recharge_date (optional), notes (optional) }`
- **Effect**: Increments `recharges_used` on the rental, rental remains `active`
- **Validation**: Returns 400 if max recharges already reached; 400 if rental is not active

### Files changed

| File | Change |
|------|--------|
| `frontend/src/components/RentalReturnDialog.vue` | Added recharge banner + `canRecharge` computed + `onRecharge` handler |
| `frontend/src/services/api.js` | `batteryRentalsAPI.recordRecharge` already existed |
| `models.py` | `BatteryRental.max_recharges`, `BatteryRental.recharges_used` already existed |
| `api/app/main.py` | `POST /battery-rentals/{rental_id}/recharge` already existed |

---

## Auto-Return When Battery Goes on Charge

### Overview

If a customer physically returns a battery to the hub but an operator has not yet marked it as returned in the system, the app will now automatically close the rental when the battery's telemetry shows it is being charged.

### How it works

When a live data reading arrives via webhook and shows positive current (`current_amps > 0` or `charger_current > 0`), the system:

1. Queries for any active `BatteryRental` linked to that battery with no `actual_return_date`
2. Sets `rental.actual_return_date = telemetry timestamp`
3. Sets `rental.status = 'returned'` and `item.returned_at = telemetry timestamp`
4. Logs an `auto_return_on_charge` event for audit purposes

This runs silently inside the webhook handler — no operator action required.

### Files changed

| File | Change |
|------|--------|
| `api/app/main.py` | Added auto-return block inside `handle_direct_format()` after LiveData is saved |

---

## Rental Form Dropdowns: Stale Cache Fix

### Problem

The customer and battery dropdowns in the rental creation forms (battery and PUE) could appear empty after a period of inactivity or after certain page navigations, even though data was present in the database. This was caused by the SWR (stale-while-revalidate) offline cache serving a stale empty response.

### Fix

Critical form dropdowns now bypass the SWR cache and always fetch fresh data from the server when the form opens. This applies to:

- Battery list (available batteries for selection)
- Customer/user list

Read-only list pages (Rentals, Batteries, Users) still use SWR since briefly showing slightly stale data there is acceptable and improves performance.

### Rule for future development

Any `GET` that populates a **required form dropdown** (where empty = user is blocked from completing the workflow) should include `_bypassOffline: true` on the axios request config.

### Files changed

| File | Change |
|------|--------|
| `frontend/src/components/BatteryRentalForm.vue` | `loadUsers` and `loadBatteries` now use `_bypassOffline: true` |
| `frontend/src/components/PUERentalForm.vue` | `loadUsers` now uses `_bypassOffline: true` |
| `frontend/src/components/SwapBatteryDialog.vue` | `loadAvailableBatteries` now uses `_bypassOffline: true` |
| `frontend/src/components/BatteryRentalForm.vue` | Cost structures no longer filtered out when battery list is temporarily empty |

---

## User Report Builder (Data Page)

### Overview

A new **Report Builder** tab on the Data page generates per-user analytics reports covering rental history, power usage, and daily breakdowns.

### Features

- Select a user and date range, then click **Generate Report**
- **Summary cards** with mean/median toggle (± standard deviation) for:
  - Total rentals and days with rentals
  - Rentals per active day
  - Average rental duration (hours)
  - Average discharge power (W) — excludes charging periods
  - Average Wh discharged per active day
- **Daily breakdown table** with per-rental sub-rows showing battery, time range, duration, status, and power stats
- **Power Usage chart** with segment colouring: teal = charging, red = discharging
- **CSV downloads** on all three tabs (Summary, Daily, Power Timeline)
- Hover tooltips on each summary card explain what the metric measures

### Power stats

All power statistics (peak W, min W, mean W, standard deviation) filter to **discharge only** (negative `power_watts` values, converted to positive). Charging periods are excluded to avoid mixing the two power flows.

### Backend

- **Endpoint**: `POST /analytics/user-report`
- **Body**: `{ user_id, start_date, end_date, hub_id }`
- **Returns**: `{ summary, daily, rentals, power_timeline }`
- Uses trapezoidal integration over discharge-only segments to estimate Wh consumed

### Files changed

| File | Change |
|------|--------|
| `api/app/main.py` | Added `POST /analytics/user-report` endpoint |
| `frontend/src/pages/DataPage.vue` | Added Report Builder tab with summary cards, table, chart, CSV downloads |
| `frontend/src/services/api.js` | Added `analyticsAPI.userReport()` |

---

## Telemetry Chart Improvements (Data Page)

### Current (A) chart

The current amperage chart now uses **segment colouring**:
- **Teal** when current is positive (battery charging)
- **Red** when current is negative (battery discharging / in use)

A bold horizontal line marks zero for easy visual reference.

### GPS Track

Seed data for DEV-001 now includes GPS coordinates (near Kindia, Guinea) so the GPS Track tab on the Data page shows a realistic map trail. ~75% of data points have coordinates; the remainder simulate GPS signal loss.
