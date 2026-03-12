# Changelog - March 2026

## Summary

21 bugs and feature requests implemented across 4 phases, covering mobile UI fixes, offline sync reliability, new features (customers page, survey improvements, form enhancements), infrastructure (database backups), and payment collection at rental time. All changes are frontend-only unless noted; some features require corresponding backend updates (see Backend Changes Needed below).

---

## Phase 1: Mobile UI & CSS Fixes

### Mobile form overflow fixed
- **Problem**: Forms (user creation, rental, PUE, cost structures) overflowed the screen edge on mobile devices, making them impossible to read or scroll.
- **Fix**: Added global CSS rules in `frontend/src/css/app.css` constraining dialogs to 95vw/90vh, enabling overflow scrolling on card sections, and ensuring inputs never exceed container width.
- **Files**: `frontend/src/css/app.css`

### PWA screen rotation unlocked
- **Problem**: The installed PWA was locked to portrait orientation.
- **Fix**: Changed `orientation: 'portrait'` to `orientation: 'any'` in `frontend/quasar.config.js`.
- **Files**: `frontend/quasar.config.js`

---

## Phase 2: Offline/Sync Improvements

### Stale-while-revalidate for faster page loads
- **Problem**: On weak signal, users waited for network timeout before seeing data.
- **Fix**: When online with cached data available, the app now returns cached data immediately and revalidates in the background. A brief teal "Updated" chip appears when fresh data arrives.
- **Files**: `frontend/src/services/offlineInterceptor.js`, `frontend/src/layouts/MainLayout.vue`

### Cost structures available offline
- **Problem**: Creating a cost structure offline didn't make it available in rental form dropdowns.
- **Fix**: Added optimistic handler for cost structure creation that generates a temp ID and merges the synthetic structure into the cached list immediately.
- **Files**: `frontend/src/services/offlineOptimistic.js`

### Stay logged in while offline
- **Problem**: Users got logged out when connectivity dropped because network errors triggered the 401 logout handler.
- **Fix**: The 401 interceptor now only triggers logout when a real server response (HTTP 401) is received, not on network errors.
- **Files**: `frontend/src/services/api.js`

### Failed sync visibility and actions
- **Problem**: Failed offline mutations were invisible to users, with no way to retry or discard them.
- **Fix**: Added `getFailedMutations()` and `getFailedMutationCount()` to offlineDb. SyncManager now tracks `failedCount` in reactive state and exports `retryFailedMutation()` and `discardFailedMutation()`. MainLayout shows a red chip when failures exist; clicking opens a dialog listing each failed mutation with Retry and Discard buttons.
- **Files**: `frontend/src/services/offlineDb.js`, `frontend/src/services/syncManager.js`, `frontend/src/layouts/MainLayout.vue`

### PUE "rented" status blocked on create
- **Problem**: Users could create a PUE with status "rented" which didn't create a rental record, causing data inconsistency.
- **Fix**: Removed "rented" from the status options in the Add PUE form. To rent a PUE, users must create a rental separately.
- **Files**: `frontend/src/pages/PUEPage.vue`

### ESM import compatibility
- Fixed `.js` extensions on all internal service imports (`offlineDb`, `offlineOptimistic`) so tests can run under Node ESM without Quasar's bundler aliases.
- **Files**: `frontend/src/services/syncManager.js`, `frontend/src/services/offlineInterceptor.js`, `frontend/src/services/cacheWarmer.js`

---

## Phase 3: Feature Additions

### Customers page
- **Problem**: No dedicated view for customer-role users.
- **Fix**: Added a "Customers" route (`/customers`) that renders UsersPage filtered to `role: 'user'`. Added Customers nav item in the sidebar under Management. Page title changes dynamically based on context.
- **Files**: `frontend/src/router/routes.js`, `frontend/src/layouts/MainLayout.vue`, `frontend/src/pages/UsersPage.vue`

### Hub managers see only customers
- Hub admin users (`role: hub_admin`) now automatically see only customer-role users in any user list, regardless of which page they navigate to.
- **Files**: `frontend/src/pages/UsersPage.vue`

### Survey CSV timeframe selection
- **Problem**: Survey export always exported all data with no date filtering.
- **Fix**: Added a timeframe selector with presets (Last Week, Last Month, Last 3 Months, All Data) and a Custom option with start/end date pickers. Date params are passed to the export API.
- **Files**: `frontend/src/pages/SettingsPage.vue`

### GESI multi-select
- The GESI status field in user forms now supports selecting multiple values with chip display.
- **Files**: `frontend/src/pages/UsersPage.vue`
- **Backend needed**: Store as JSON array or comma-separated in existing `gesi_status` Text column.

### Monthly energy split into electricity + heat
- Replaced the single "Monthly Energy Expenditure" field with two separate fields: "Monthly Electricity Spend" and "Monthly Heat/Other Spend".
- **Files**: `frontend/src/pages/UsersPage.vue`
- **Backend needed**: Add `monthly_energy_electricity` and `monthly_energy_heat` Float columns via Alembic migration.

### Signup reason multi-select
- The signup reason field now supports selecting multiple values with chip display.
- **Files**: `frontend/src/pages/UsersPage.vue`
- **Backend needed**: Store as JSON array or comma-separated in existing Text column.

### Decimal durations in cost structures
- Duration option values (default, min, max) and dropdown choice values now accept decimal input with `step="0.01"`.
- **Files**: `frontend/src/pages/SettingsPage.vue`
- **Backend needed**: Change `default_value`, `min_value`, `max_value` columns from Integer to Float via Alembic migration.

---

## Phase 4: Complex Features

### Database backup and restore scripts
- Created three scripts:
  - `scripts/backup_db.sh` - Creates timestamped gzipped backups, retains 30 days
  - `scripts/restore_db.sh` - Restores from a backup file with confirmation prompt
  - `scripts/test_backup_restore.sh` - Creates backup, restores into temp DB, verifies table count, cleans up
- Added Makefile targets: `make db-backup`, `make db-restore FILE=path`, `make db-backup-test`
- **Files**: `scripts/backup_db.sh`, `scripts/restore_db.sh`, `scripts/test_backup_restore.sh`, `Makefile`

### Pay on rental (upfront payment collection)
- **Problem**: No way to collect payment at rental creation time.
- **Fix**: Both BatteryRentalForm and PUERentalForm now show a payment collection section when the selected cost structure has upfront charges. Displays the amount due, a payment method selector (Cash, Mobile Money, Bank Transfer, Card), and a pre-filled payment amount field. Payment data is included in the rental creation payload.
- **Files**: `frontend/src/components/BatteryRentalForm.vue`, `frontend/src/components/PUERentalForm.vue`
- **Backend needed**: Create `AccountTransaction` with payment data when rental is created with upfront payment.

### Unified test target
- Added `make test-all` that runs frontend offline tests + frontend build verification in one command.
- **Files**: `Makefile`

---

## Tests

38 new tests added to `frontend/test-offline.mjs` (total: 108 tests), covering:

- Failed mutation tracking (getFailedMutations, getFailedMutationCount)
- Cost structure optimistic handler (create, cache merge, URL recognition)
- Stale-while-revalidate interceptor exports
- SyncManager failedCount, retry, and discard logic
- PUE status options (no "rented")
- API 401 guard (network errors don't logout)
- Customers route and roleFilter prop
- GESI and signup reason multi-select
- Monthly energy split fields
- Survey export timeframe selector
- Decimal duration values
- PWA orientation setting
- Mobile CSS overflow fixes
- Pay on rental (upfront payment fields in both forms)
- MainLayout sync UI (failed chip, cache-updated, customers nav)
- Backup scripts existence and content
- Makefile test-all target

Run with: `make frontend-test-offline` or `make test-all`

---

## Phase 5: Backend Updates & Deposit System

### Alembic Migration
- **Migration**: `a1b2c3d4e5f6_add_energy_split_decimal_durations_deposit_holds.py`
- Adds `monthly_energy_electricity` (Float) and `monthly_energy_heat` (Float) to user table
- Alters `default_value`, `min_value`, `max_value` from Integer to Float on `cost_structure_duration_options`
- Creates `deposit_holds` table for credit hold system
- **Files**: `alembic/versions/a1b2c3d4e5f6_...py`, `models.py`

### GESI & Signup Reason Multi-Select (Backend)
- Pydantic schemas now accept `Union[str, List[str]]` for `gesi_status` and `main_reason_for_signup`
- Lists are joined with commas for storage, split back to lists on retrieval
- Backward compatible: string values still work
- User endpoints (create, update, get, list) now use `serialize_user()` helper
- **Files**: `api/app/main.py`

### Monthly Energy Split (Backend)
- `UserCreate`/`UserUpdate` accept `monthly_energy_electricity` and `monthly_energy_heat`
- Auto-computes `monthly_energy_expenditure` as sum of both fields
- Update handler uses existing values when only one field is changed
- **Files**: `api/app/main.py`, `models.py`

### Decimal Duration Support (Backend)
- Duration option columns changed from Integer to Float in both model and migration
- Supports values like 0.5 months
- **Files**: `models.py`, migration

### Upfront Payment on Rental (Backend)
- Battery rental creation now accepts `upfront_payment: {payment_amount, payment_method}`
- When provided, creates payment + charge transactions on user account
- Updates rental's `amount_paid`, `payment_method`, `payment_type` fields
- Response includes `upfront_charges` array with payment details
- **Files**: `api/app/main.py`

### Deposit Hold System
- **New model**: `DepositHold` tracks credit holds for active rental deposits
- **Rental creation**: If cost structure has `deposit_amount > 0`, creates a deposit hold against user's account credit
- Validates available credit (balance minus existing held deposits) before creating hold
- Returns 400 "Insufficient credit for deposit" if credit is too low
- Creates low-credit notification if remaining available credit goes negative
- **Rental return**: Automatically releases deposit hold (sets status='released', records released_at)
- Works for both battery and PUE rentals
- **New endpoints**:
  - `GET /accounts/user/{user_id}/deposit-holds` - list deposit holds (filterable by status)
  - `GET /accounts/user/{user_id}/credit-summary` - returns balance, held_deposits, available_credit, active holds
- **Frontend**: UserDetailPage shows Credit & Deposits card with balance, held deposits, available credit, and active holds table
- **Frontend**: BatteryRentalForm and PUERentalForm show credit check banners (green/orange) when cost structure requires a deposit
- **Files**: `models.py`, `api/app/main.py`, `frontend/src/services/api.js`, `frontend/src/pages/UserDetailPage.vue`, `frontend/src/components/BatteryRentalForm.vue`, `frontend/src/components/PUERentalForm.vue`

### Integration Test Script
- Full user flow tests: auth, user CRUD with new fields, battery/PUE rental lifecycle with deposits, insufficient credit edge case, decimal durations
- Run with `make test-user-flows` (requires running backend)
- **Files**: `scripts/test_user_flows.py`, `Makefile`

### Offline Cache Invalidation
- Rental mutations now also invalidate `GET:/accounts/` cache to refresh deposit holds and credit summaries
- **Files**: `frontend/src/services/syncManager.js`

---

## Backend Changes Still Needed

1. **Survey export timeframe**: Ensure export endpoint accepts `start_date` and `end_date` query parameters (may already be supported)

---

## Files Modified

| File | Changes |
|------|---------|
| `frontend/src/css/app.css` | Global mobile overflow fixes |
| `frontend/quasar.config.js` | PWA orientation unlocked |
| `frontend/src/services/offlineInterceptor.js` | Stale-while-revalidate, ESM import fix |
| `frontend/src/services/offlineOptimistic.js` | Cost structure optimistic handler |
| `frontend/src/services/offlineDb.js` | getFailedMutations, getFailedMutationCount |
| `frontend/src/services/syncManager.js` | failedCount, retry/discard exports, ESM import fix |
| `frontend/src/services/cacheWarmer.js` | ESM import fix |
| `frontend/src/services/api.js` | 401 interceptor: only logout on real server 401 |
| `frontend/src/layouts/MainLayout.vue` | Failed sync chip/dialog, cache-updated chip, Customers nav |
| `frontend/src/pages/PUEPage.vue` | Removed "rented" from status options |
| `frontend/src/router/routes.js` | Added customers route |
| `frontend/src/pages/UsersPage.vue` | roleFilter prop, hub_admin filtering, GESI/signup multi-select, energy split |
| `frontend/src/pages/SettingsPage.vue` | Survey timeframe selector, decimal duration steps |
| `frontend/src/components/BatteryRentalForm.vue` | Upfront payment collection, deposit credit check banner |
| `frontend/src/components/PUERentalForm.vue` | Upfront payment collection, deposit credit check banner |
| `frontend/src/pages/UserDetailPage.vue` | Credit & Deposits card |
| `frontend/src/services/syncManager.js` | Rental mutations invalidate accounts cache |
| `frontend/test-offline.mjs` | 41 new tests (111 total) |
| `models.py` | Energy split columns, DepositHold model, Float duration columns |
| `api/app/main.py` | Schema updates, upfront payment, deposit holds, user serialization, new endpoints |
| `Makefile` | db-backup, db-restore, db-backup-test, test-all, test-user-flows targets |

## Files Created

| File | Purpose |
|------|---------|
| `scripts/backup_db.sh` | Database backup script |
| `scripts/restore_db.sh` | Database restore script |
| `scripts/test_backup_restore.sh` | Backup/restore verification script |
| `scripts/test_user_flows.py` | Full user flow integration tests |
| `alembic/versions/a1b2c3d4e5f6_...py` | Database migration for energy split, decimal durations, deposit holds |
| `docs/CHANGELOG_2026_03.md` | This changelog |
