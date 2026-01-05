# Frontend Implementation Plan - Rental System Restructure

## Overview
This document outlines the complete frontend implementation plan for the rental system restructure. The backend has been fully implemented with separate Battery and PUE rental systems, pay-to-own functionality, and inspection tracking.

## Backend Changes (Completed)
- ✅ Separated battery and PUE rentals into distinct tables/systems
- ✅ Added pay-to-own support for PUE items with ledger tracking
- ✅ Implemented inspection tracking for PUE items
- ✅ Added new cost structure configuration tables
- ✅ Created 12 new API endpoints for battery rentals, PUE rentals, and inspections
- ✅ Updated CostComponent to support new unit types: per_week, per_month, per_recharge, one_time

## Frontend Implementation Phases

### Phase 1: Update API Service Layer ⭐ CRITICAL PATH
**File**: `frontend/src/services/api.js`

#### Add batteryRentalsAPI object:
```javascript
batteryRentalsAPI: {
  create: (data) => api.post('/battery-rentals', data),
  get: (rentalId) => api.get(`/battery-rentals/${rentalId}`),
  return: (rentalId, data) => api.post(`/battery-rentals/${rentalId}/return`, data),
  addBattery: (rentalId, batteryId) => api.post(`/battery-rentals/${rentalId}/add-battery`, { battery_id: batteryId }),
  recordRecharge: (rentalId, data) => api.post(`/battery-rentals/${rentalId}/recharge`, data)
}
```

#### Add pueRentalsAPI object:
```javascript
pueRentalsAPI: {
  create: (data) => api.post('/pue-rentals', data),
  get: (rentalId) => api.get(`/pue-rentals/${rentalId}`),
  recordPayment: (rentalId, data) => api.post(`/pue-rentals/${rentalId}/payment`, data),
  getPayToOwnLedger: (rentalId) => api.get(`/pue-rentals/${rentalId}/pay-to-own-ledger`)
}
```

#### Add pueInspectionsAPI object:
```javascript
pueInspectionsAPI: {
  create: (pueId, data) => api.post(`/pue/${pueId}/inspections`, data),
  list: (pueId) => api.get(`/pue/${pueId}/inspections`),
  getDue: (params) => api.get('/inspections/due', { params }),
  getOverdue: (params) => api.get('/inspections/overdue', { params })
}
```

### Phase 2: Core Rental Pages ⭐ CRITICAL PATH

#### 2.1 Create CreateBatteryRentalPage.vue
**Purpose**: New page for creating battery rentals

**Features**:
- User selection (searchable dropdown)
- Multiple battery selection (checkboxes or multi-select)
- Cost structure selection
- Rental start date picker
- Due date picker
- Deposit amount input
- Notes textarea
- Real-time cost calculation preview

**Components to use**:
- q-select (user selection)
- q-select (battery selection with multiple)
- q-select (cost structure)
- q-date (dates)
- q-input (deposit, notes)

#### 2.2 Create CreatePUERentalPage.vue
**Purpose**: New page for creating PUE rentals with pay-to-own option

**Features**:
- User selection (searchable dropdown)
- Single PUE selection
- Cost structure selection
- Rental start date picker
- Pay-to-own toggle
- Conditional pay-to-own fields:
  - Total price
  - Initial payment
  - Payment schedule preview
- Notes textarea
- Real-time cost calculation

**Components to use**:
- q-select (user, PUE, cost structure)
- q-toggle (pay-to-own switch)
- q-date (rental start)
- q-input (price, payment)

#### 2.3 Update UserDetailPage.vue ⭐ CRITICAL PATH
**File**: `frontend/src/pages/UserDetailPage.vue` (1845 lines)

**Changes**:
- Split rental display into two tabs:
  - **Battery Rentals Tab**: Show active/past battery rentals
  - **PUE Rentals Tab**: Show active/past PUE rentals with pay-to-own status
- Update "Create Rental" button to offer choice:
  - "New Battery Rental" → routes to CreateBatteryRentalPage
  - "New PUE Rental" → routes to CreatePUERentalPage
- Update rental list to use new endpoints:
  - Battery rentals: GET /battery-rentals?user_id={userId}
  - PUE rentals: GET /pue-rentals?user_id={userId}
- Add pay-to-own progress bar for PUE rentals
- Add inspection status indicators for PUE items

#### 2.4 Update RentalsPage.vue
**File**: `frontend/src/pages/RentalsPage.vue`

**Decision**: Either deprecate or update to aggregate view
- **Option A**: Deprecate and redirect to separate battery/PUE rental pages
- **Option B**: Update to show combined view with filters:
  - Filter by type: Battery / PUE / All
  - Use both endpoints and merge results
  - Color-code by type

**Recommendation**: Option B for backward compatibility

#### 2.5 Update RentalDetailPage.vue
**File**: `frontend/src/pages/RentalDetailPage.vue`

**Changes**:
- Detect rental type from route/params
- Load from appropriate endpoint:
  - Battery: GET /battery-rentals/{id}
  - PUE: GET /pue-rentals/{id}
- Show type-specific fields:
  - **Battery**: Recharge history, multiple items
  - **PUE**: Single item, pay-to-own ledger, inspection history
- Update return dialog to use appropriate return endpoint

### Phase 3: PUE Inspection Features

#### 3.1 Update PUEPage.vue (List View)
**File**: `frontend/src/pages/PUEPage.vue`

**Changes**:
- Add "Inspection Status" column with color coding:
  - ✅ Green: Inspected recently
  - ⚠️ Yellow: Due soon (within 7 days)
  - ❌ Red: Overdue
- Add inspection filters:
  - All / Due / Overdue
- Add "Schedule Inspection" bulk action
- Add last inspection date column

#### 3.2 Create PUE Detail Inspection UI
**Location**: Within PUE detail page/dialog

**Features**:
- Inspection history table
- "Record New Inspection" button
- Inspection form:
  - Inspector name
  - Inspection date
  - Condition dropdown: Excellent/Good/Fair/Poor/Damaged
  - Notes
  - Requires maintenance checkbox
  - Maintenance notes (conditional)
- Next inspection due date display

#### 3.3 Dashboard Inspection Alerts
**File**: `frontend/src/pages/DashboardPage.vue`

**Changes**:
- Add "Inspections Due" widget showing count
- Add "Overdue Inspections" widget with warning
- Click to filter PUE list page

### Phase 4: Settings & Configuration

#### 4.1 Update SettingsPage.vue
**File**: `frontend/src/pages/SettingsPage.vue`

**Changes**:
- Add "Cost Structure Configuration" section
- Battery Rental Configuration:
  - Grace period days (per cost structure)
  - Overdue fine per day
  - Maximum recharges allowed
- PUE Rental Configuration:
  - Inspection interval days
  - Pay-to-own eligibility toggle
  - Default payment terms
- Save to `cost_structure_battery_config` and `cost_structure_pue_config` tables

**API Integration**:
- Create endpoints: PUT /cost-structures/{id}/battery-config
- Create endpoints: PUT /cost-structures/{id}/pue-config

### Phase 5: Supporting Pages

#### 5.1 Update BatteryDetailPage.vue
**File**: `frontend/src/pages/BatteryDetailPage.vue`

**Changes**:
- Update rental history to show new battery rental format
- Display current rental from battery_rentals table
- Show recharge count for current rental
- Link to new battery rental detail page

#### 5.2 Update DashboardPage.vue
**File**: `frontend/src/pages/DashboardPage.vue`

**Changes**:
- Split rental metrics:
  - "Active Battery Rentals" count
  - "Active PUE Rentals" count
  - "Pay-to-Own Progress" aggregate
- Add inspection metrics:
  - "Inspections Due This Week"
  - "Overdue Inspections" (warning if > 0)
- Update overdue calculations for new rental types

#### 5.3 Update RentalsPageWithQR.vue
**File**: `frontend/src/pages/RentalsPageWithQR.vue`

**Changes**:
- Update QR code handling to work with new rental types
- Route to appropriate detail page based on type
- Update endpoint calls to new battery/PUE rental endpoints

#### 5.4 Update RentalReturnDialog.vue
**File**: `frontend/src/pages/RentalReturnDialog.vue`

**Changes**:
- Detect rental type (battery vs PUE)
- For battery rentals:
  - Allow partial returns (select which batteries)
  - Show recharge count
  - Calculate cost based on recharges + days
  - Use POST /battery-rentals/{id}/return
- For PUE rentals:
  - Show pay-to-own balance if applicable
  - Condition assessment
  - Use POST /pue-rentals/{id}/return (needs to be added to backend)

### Phase 6: Router & Navigation

#### 6.1 Update Router
**File**: `frontend/src/router/routes.js`

**Add Routes**:
```javascript
{
  path: '/rentals/battery/create',
  component: () => import('pages/CreateBatteryRentalPage.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/rentals/pue/create',
  component: () => import('pages/CreatePUERentalPage.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/rentals/battery/:id',
  component: () => import('pages/BatteryRentalDetailPage.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/rentals/pue/:id',
  component: () => import('pages/PUERentalDetailPage.vue'),
  meta: { requiresAuth: true }
}
```

#### 6.2 Update Navigation Menu
**File**: `frontend/src/layouts/MainLayout.vue`

**Changes**:
- Update "Rentals" menu to submenu:
  - All Rentals
  - Battery Rentals
  - PUE Rentals
  - Create Battery Rental
  - Create PUE Rental

## Testing Checklist

### Battery Rental Testing
- [ ] Create new battery rental with multiple batteries
- [ ] View battery rental details
- [ ] Add battery to existing rental
- [ ] Record recharge for rental
- [ ] Return single battery from rental
- [ ] Return all batteries from rental
- [ ] View rental history on battery detail page
- [ ] View user's battery rentals on user detail page

### PUE Rental Testing
- [ ] Create standard PUE rental
- [ ] Create pay-to-own PUE rental
- [ ] Record payment on pay-to-own rental
- [ ] View pay-to-own ledger progress
- [ ] View PUE rental details
- [ ] View user's PUE rentals on user detail page

### Inspection Testing
- [ ] Record new inspection for PUE
- [ ] View inspection history
- [ ] View inspections due list
- [ ] View overdue inspections list
- [ ] See inspection status on PUE list page
- [ ] Dashboard shows correct inspection counts

### Settings Testing
- [ ] Configure battery rental settings per cost structure
- [ ] Configure PUE rental settings per cost structure
- [ ] Verify settings applied to new rentals

### Integration Testing
- [ ] Cost calculations correct for new unit types (per_week, per_month, per_recharge, one_time)
- [ ] Overdue calculations work with grace periods
- [ ] Dashboard aggregates show correct totals
- [ ] All navigation links work
- [ ] QR code scanning routes correctly
- [ ] Return dialogs work for both types

## Implementation Order (Critical Path First)

1. **Phase 1**: API Service Layer (blocks everything)
2. **Phase 2.3**: UserDetailPage updates (most frequently used)
3. **Phase 2.1**: CreateBatteryRentalPage
4. **Phase 2.2**: CreatePUERentalPage
5. **Phase 3**: PUE Inspection Features
6. **Phase 5.2**: DashboardPage updates
7. **Phase 2.5**: RentalDetailPage updates
8. **Phase 5**: Remaining supporting pages
9. **Phase 6**: Router & Navigation
10. **Phase 4**: Settings & Configuration (can be done last)

## Notes

### Backward Compatibility
- Keep old `/rentals` endpoints working temporarily
- Add deprecation warnings in console
- Provide migration period before removing old code

### Data Migration
- No frontend data migration needed
- Backend migration already completed
- Old rental data deleted as agreed

### New Unit Types
Ensure cost calculation functions handle:
- `per_week`: Calculate weeks from rental period
- `per_month`: Calculate months from rental period
- `per_recharge`: Multiply by recharge count
- `one_time`: Charged once regardless of duration

### Pay-to-Own UI/UX
- Clear progress indicator (progress bar)
- Show: Paid / Total / Remaining
- Payment history table
- Next payment due date (if recurring)
- Option to pay off early

### Inspection Intervals
- Configurable per cost structure (e.g., 30 days, 90 days)
- Calculate next due date from last inspection
- Grace period before marking overdue (e.g., 7 days)

## Success Criteria
- ✅ All new rental types can be created through UI
- ✅ Users can view separate battery and PUE rental histories
- ✅ Pay-to-own functionality fully working
- ✅ Inspection tracking complete
- ✅ All cost calculation types work correctly
- ✅ Dashboard shows accurate metrics
- ✅ No console errors
- ✅ All old rentalsAPI calls replaced
- ✅ Complete test coverage
