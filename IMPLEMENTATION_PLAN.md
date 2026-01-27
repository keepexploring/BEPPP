# Implementation Plan: System Enhancements

## Overview
This plan covers 7 major enhancement areas for the solar battery rental system:
1. Survey Responses - Fix export and add dedicated page
2. Dashboard Simplification - Streamline metrics and actions
3. User Role Renaming - Change "user" role display to "customer"
4. New Hub Admin Role - Add hub_admin role with limited permissions
5. Permission System Fixes - Properly restrict capabilities by role
6. Battery Webhook Testing - Verify data submission works
7. Analytics Review - (Deferred to later)

---

## TASK 1: Survey Responses System

### Current State
- Survey system fully implemented with database tables, API endpoints, and UI
- Export endpoint exists at `/return-survey/responses/export` (main.py:9392-9492)
- Export button exists in SettingsPage.vue (line 242)
- Export function implemented (lines 3520-3561)
- **Issue**: Export button doesn't work or download fails

### Implementation Steps

#### 1.1 Debug and Fix Export Functionality
**Files**:
- `api/app/main.py` (lines 9392-9492)
- `frontend/src/pages/SettingsPage.vue` (lines 3520-3561)

**Actions**:
1. Test export endpoint directly to verify backend works
2. Check browser console for JavaScript errors during export
3. Verify CSV generation with test data
4. Add error logging to identify failure point
5. Fix identified issues (likely related to empty results or CORS)

#### 1.2 Create Survey Responses Page
**New File**: `frontend/src/pages/SurveyResponsesPage.vue`

**Features**:
- Table display of all survey responses
- Filters: Hub, Rental Type (Battery/PUE), Date Range
- Columns: Response ID, Rental Type, Rental ID, User, Question, Answer, Date
- Export CSV button (prominent placement)
- Pagination for large datasets
- Permission: Admins and Superadmins only

**API Endpoints** (already exist):
- `GET /return-survey/responses` - List responses
- `GET /return-survey/responses/export` - Export CSV

#### 1.3 Add Menu Item
**File**: `frontend/src/layouts/MainLayout.vue`

**Actions**:
1. Add new menu item "Survey Responses" with icon "poll" or "feedback"
2. Place after "Rentals" menu item
3. Set `requiresAdmin: true` in route guard
4. Link to `{ name: 'survey-responses' }`

#### 1.4 Add Route
**File**: `frontend/src/router/routes.js`

**Actions**:
1. Add route definition:
```javascript
{
  path: '/survey-responses',
  name: 'survey-responses',
  component: () => import('pages/SurveyResponsesPage.vue'),
  meta: { requiresAuth: true, requiresAdmin: true }
}
```

---

## TASK 2: Dashboard Simplification

### Current State
- Dashboard located at `frontend/src/pages/DashboardPage.vue`
- Shows 4 metrics: Total Hubs, Active Batteries, Active Rentals, Total Revenue
- Quick actions: New Rental, Returns, Add Battery, View Analytics
- Alerts section with rental alerts (working)
- Hub summary section

### Changes Required

#### 2.1 Modify Metrics Section
**File**: `frontend/src/pages/DashboardPage.vue`

**Keep**:
- Total Hubs (no change)
- Active Rentals → Rename to "Batteries Out for Rental"

**Add NEW metric**:
- "Batteries Ready for Rental"
  - Count batteries with status='available' AND NOT in maintenance
  - Backend: Query `BEPPPBattery` where `status = 'available'` for filtered hubs
  - May need new backend endpoint or modify `/analytics/hub-summary`

**Remove**:
- Total Revenue metric (delete entire card)

#### 2.2 Restructure Page Layout
**File**: `frontend/src/pages/DashboardPage.vue`

**New Order**:
1. **Quick Actions** (move to top, just below header)
   - Battery Rental (route to create battery rental)
   - PUE Rental (route to create PUE rental)
   - Returns (route to rentals page with returns action)
   - Remove: Add Battery, View Analytics

2. **Metrics Cards** (below quick actions)
   - Total Hubs
   - Batteries Out for Rental
   - Batteries Ready for Rental

3. **Alerts Section** (move to bottom)
   - Overdue Rentals
   - Upcoming Rentals
   - PUE Inspections (if working)

4. **Hub Summary** (keep at bottom)

#### 2.3 Fix PUE Inspection Alerts
**Files**:
- `api/app/main.py` (modify `/hubs/{hub_id}/pue` endpoint)
- `frontend/src/pages/DashboardPage.vue`

**Issue**: Backend doesn't return `inspection_status` field

**Fix**:
1. Add calculation in backend endpoint to determine inspection status:
   - If `next_inspection_due < now`: status = "overdue"
   - If `next_inspection_due <= now + 3 days`: status = "due_soon"
2. Return `inspection_status` and `last_inspection_date` fields
3. Frontend already expects and filters by these fields

---

## TASK 3: Rename "User" Role to "Customer"

### Current State
- Role stored as "user" in database `user.user_access_level` field
- UserRole enum: `USER = "user"` (models.py:11)
- Term "user" refers to the general concept throughout
- Role "user" is the first/lowest access level (kiosk operators)

### Implementation Strategy
**Database**: Keep role value as "user" in database (no migration needed)
**Display**: Change display label from "User" to "Customer" in UI only

### Changes Required

#### 3.1 Frontend Display Changes
**Files to modify**:
- `frontend/src/pages/UsersPage.vue` - User list table role column
- `frontend/src/pages/UserDetailPage.vue` - User detail display
- `frontend/src/pages/AccountsPage.vue` - Accounts table role display
- `frontend/src/components/*` - Any component showing user roles
- `frontend/src/stores/auth.js` - Role display getter (if needed)

**Strategy**: Create display label mapping
```javascript
const roleLabels = {
  'user': 'Customer',
  'admin': 'Admin',
  'superadmin': 'Super Admin',
  'battery': 'Battery',
  'data_admin': 'Data Admin',
  'hub_admin': 'Hub Admin'  // new role
}
```

#### 3.2 Form/Selector Changes
**Files**:
- Any user creation/edit forms with role dropdowns
- Settings pages with role filters

**Action**: Update option labels while keeping values as "user"

---

## TASK 4: Add New Hub Admin Role

### Implementation Steps

#### 4.1 Add Role to Enum
**File**: `models.py` (lines 10-15)

**Change**:
```python
class UserRole(enum.Enum):
    USER = "user"           # Customer - kiosk operator
    HUB_ADMIN = "hub_admin"  # Hub administrator - daily operations
    ADMIN = "admin"         # Admin (everything except webhook)
    SUPERADMIN = "superadmin"  # Can do everything
    BATTERY = "battery"     # Can only write to webhook
    DATA_ADMIN = "data_admin"  # Can only view data analytics, no user info
```

#### 4.2 Database Migration
**Create new migration file**: `alembic/versions/YYYYMMDD_add_hub_admin_role.py`

**Actions**:
1. No schema changes needed (role column already allows any string)
2. Migration just documents the new role value

#### 4.3 Frontend Role Support
**Files**:
- `frontend/src/stores/auth.js` - Add `isHubAdmin` getter
- `frontend/src/pages/UsersPage.vue` - Add to role dropdown options
- Any role selection components

---

## TASK 5: Fix Permission System with Role Hierarchy

### Role Hierarchy Definition

#### 5.1 SUPERADMIN (Highest Access)
**Can do**:
- Everything (no restrictions)
- Add/Edit/Delete hubs
- Manage all users across all hubs
- Access all data
- Configure system settings
- Manage permissions
- Grant hub access to data_admins
- Access webhooks

**Cannot do**: Nothing (full access)

#### 5.2 ADMIN (Hub-Level Full Access)
**Can do**:
- Add/Edit/Delete batteries (own hub only)
- Add/Edit/Delete PUE equipment (own hub only)
- Create/Modify/Delete rentals (own hub only)
- Add/Edit/Delete users (own hub, but cannot create superadmins)
- View accounts (own hub only)
- Access settings for own hub
- View analytics (own hub only)
- Manage cost structures (own hub only)
- Create job cards (own hub only)
- View survey responses (own hub only)

**Cannot do**:
- Add/Edit/Delete hubs
- Access other hubs' data
- Create superadmin users
- Grant hub access to data_admins

#### 5.3 HUB_ADMIN (NEW - Daily Operations)
**Can do**:
- Create battery rentals (own hub only)
- Create PUE rentals (own hub only)
- Process rental returns (own hub only)
- View rental table and status (own hub only)
- Add customers/users (user role only, own hub)
- View user list (own hub only)
- View simple dashboard (rentals, due dates)
- View what's currently rented and due back

**Cannot do**:
- Add/Edit/Delete batteries or PUE
- Delete rentals
- Edit users (except customers they created)
- Access settings
- Access accounts
- View analytics
- Create job cards
- Access webhooks
- View survey responses
- Add admin-level users

#### 5.4 DATA_ADMIN (Analytics Only)
**Can do** (unchanged):
- View analytics across assigned hubs
- View anonymized rental data
- Export reports

**Cannot do**:
- View personal user information
- Create/Edit/Delete any entities
- Access settings

#### 5.5 USER/CUSTOMER (Lowest Access)
**Can do** (unchanged):
- View own rentals
- View own account
- Submit return surveys

**Cannot do**:
- Access admin features
- View other users
- Create rentals (handled by hub_admin or admin)

### Implementation Changes

#### 5.1 Backend Permission Guards
**File**: `api/app/main.py`

**Pattern for each endpoint**:
```python
# Example: Creating battery rental
if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.HUB_ADMIN]:
    raise HTTPException(status_code=403, detail="Insufficient permissions")

# Example: Adding hubs (superadmin only)
if current_user.get('role') != UserRole.SUPERADMIN:
    raise HTTPException(status_code=403, detail="Only superadmins can manage hubs")

# Example: Hub admin restrictions
if current_user.get('role') == UserRole.HUB_ADMIN:
    # Check they're only creating battery/PUE rentals, not modifying inventory
    raise HTTPException(status_code=403, detail="Hub admins cannot modify inventory")
```

**Endpoints to modify**:
1. Hub management (lines 2314-2536) - Only SUPERADMIN
2. User management (lines 2566-2874) - Restrict hub_admin to user creation only
3. Battery management (lines 2938-3088) - Add hub_admin restriction
4. PUE management (lines 3382-3491) - Add hub_admin restriction
5. Rental creation (lines 3761+) - Allow hub_admin
6. Settings endpoints (lines 7900+) - Restrict hub_admin
7. Accounts endpoints - Restrict hub_admin
8. Job cards - Restrict hub_admin

#### 5.2 Frontend Route Guards
**File**: `frontend/src/router/index.js`

**Add new guard**:
```javascript
const requiresFullAdmin = to.matched.some(record => record.meta.requiresFullAdmin)

if (requiresFullAdmin && !authStore.isFullAdmin) {
  next({ name: 'dashboard' })
}
```

**File**: `frontend/src/stores/auth.js`

**Add getter**:
```javascript
isFullAdmin: (state) => ['admin', 'superadmin'].includes(state.role),
isHubAdmin: (state) => state.role === 'hub_admin',
```

#### 5.3 Component Visibility
**Pattern**: Use `v-if="authStore.isFullAdmin"` for buttons/sections that hub_admins shouldn't see

**Pages to modify**:
- `BatteriesPage.vue` - Hide Add/Edit/Delete buttons for hub_admin
- `PUEPage.vue` - Hide Add/Edit/Delete buttons for hub_admin
- `SettingsPage.vue` - Restrict entire page to full admins
- `AccountsPage.vue` - Restrict to full admins
- `JobCardsPage.vue` - Restrict to full admins
- `MainLayout.vue` - Hide menu items based on role

#### 5.4 Create Hub Admin Dashboard
**Option 1**: Modify existing DashboardPage.vue with conditional rendering
**Option 2**: Create separate HubAdminDashboardPage.vue

**Hub Admin Dashboard Content**:
- Simplified metrics:
  - Batteries Out for Rental
  - Rentals Due Today
  - Overdue Rentals
- Quick Actions:
  - New Battery Rental
  - New PUE Rental
  - Process Returns
- Active Rentals Table (today's due dates highlighted)
- No hub summary, no analytics links

---

## TASK 6: Test Battery Webhook System

### Current State
- Webhook endpoint: `/webhook/live-data` (main.py:1549-1848)
- Battery auth: `/auth/battery-login` (main.py:1945-2055)
- Webhook logging to file: `logs/webhook.log`
- Database logging: `webhook_logs` table
- LiveData storage: `livedata` table

### Testing Strategy

#### 6.1 Use Existing Test Script
**File**: `scripts/test_webhook_integration.py` (if exists)

**OR create new test file**: `scripts/test_battery_submission.py`

```python
import requests
import json
from datetime import datetime

# 1. Battery Login
login_response = requests.post(
    'http://localhost:8000/auth/battery-login',
    json={
        'battery_id': '123',  # Use real battery ID from database
        'battery_secret': 'battery_secret_here'
    }
)
token = login_response.json()['access_token']

# 2. Submit Live Data
data_response = requests.post(
    'http://localhost:8000/webhook/live-data',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'id': '123',
        'soc': 85.5,
        'v': 12.4,
        'i': 2.1,
        'p': 26.0,
        't': 22.5,
        'lat': 1.23,
        'lon': 36.45,
        'd': datetime.now().strftime('%Y-%m-%d'),
        'tm': datetime.now().strftime('%H:%M:%S')
    }
)

print('Login Response:', login_response.status_code)
print('Data Response:', data_response.status_code)
print('Response:', data_response.json())
```

#### 6.2 Verification Steps
1. Run test script
2. Check `logs/webhook.log` for log entries
3. Query database:
   ```sql
   SELECT * FROM webhook_logs ORDER BY created_at DESC LIMIT 5;
   SELECT * FROM livedata ORDER BY timestamp DESC LIMIT 5;
   SELECT last_data_received FROM bepppbattery WHERE battery_id = '123';
   ```
4. Verify data appears in admin webhook logs UI (if exists)

#### 6.3 Edge Cases to Test
- Invalid battery ID
- Wrong battery secret
- Battery submitting data for different battery (403 expected)
- Malformed JSON
- Missing required fields
- Large payload (stress test)

---

## TASK 7: Analytics Review
**Status**: Deferred until tasks 1-6 complete
**Placeholder**: Will review analytics page functionality after core fixes

---

## Implementation Order

### Phase 1: Quick Wins (1-2 hours)
1. Task 3: Rename "user" to "customer" in UI (display only)
2. Task 1.1: Debug and fix survey export
3. Task 6: Run webhook tests and verify functionality

### Phase 2: New Features (3-4 hours)
4. Task 1.2-1.4: Create Survey Responses page and menu
5. Task 2.1-2.2: Simplify dashboard metrics and layout
6. Task 2.3: Fix PUE inspection alerts

### Phase 3: Permission System (4-6 hours)
7. Task 4.1-4.3: Add hub_admin role
8. Task 5.1: Update backend permission guards
9. Task 5.2-5.3: Update frontend guards and visibility
10. Task 5.4: Create hub admin dashboard
11. Full permission testing across all roles

### Phase 4: Testing & Refinement (2-3 hours)
12. End-to-end testing of all features
13. Fix any bugs discovered
14. User acceptance testing

**Total Estimated Time**: 10-15 hours

---

## Risk Assessment

### High Risk
- **Permission system changes**: Could break existing functionality if not careful
  - Mitigation: Test each role thoroughly, use feature flags if possible

### Medium Risk
- **Dashboard metric changes**: Backend might need new queries
  - Mitigation: Check if existing endpoints can provide needed data first

### Low Risk
- **UI label changes**: Low impact, easy to revert
- **Survey page**: New feature, doesn't affect existing functionality
- **Webhook testing**: Read-only verification

---

## Testing Checklist

### For Each Role
- [ ] Login as role
- [ ] Verify dashboard shows correct content
- [ ] Verify menu items visible/hidden correctly
- [ ] Test creating rentals (if permitted)
- [ ] Test editing batteries/PUE (if permitted)
- [ ] Test accessing settings (if permitted)
- [ ] Test viewing analytics (if permitted)
- [ ] Verify cannot access restricted features (403 errors)

### Survey System
- [ ] Submit survey response through rental return
- [ ] View responses in new Survey Responses page
- [ ] Filter responses by hub, type, date
- [ ] Export CSV and verify data correct
- [ ] Test as admin and superadmin

### Dashboard
- [ ] Verify 3 metrics display correctly
- [ ] Verify "Ready for Rental" count accurate
- [ ] Verify quick actions route correctly
- [ ] Verify alerts at bottom of page
- [ ] Test with different hub selections

### Webhooks
- [ ] Battery can authenticate
- [ ] Battery can submit data
- [ ] Data appears in livedata table
- [ ] Webhook logs created
- [ ] File logs contain entries
- [ ] Wrong battery ID rejected

---

## Rollback Plan

### If Major Issues Discovered
1. Git revert to pre-implementation commit
2. Deploy previous stable version
3. Document issues for future attempt

### If Partial Issues
1. Use feature flags to disable problematic features
2. Fix critical bugs in hotfix branch
3. Redeploy with fixes

---

## Success Criteria

### Must Have
- [ ] All 5 roles work correctly with proper permissions
- [ ] Survey responses viewable and exportable
- [ ] Dashboard simplified as specified
- [ ] "Customer" label used instead of "user" role
- [ ] Battery webhook verified working

### Nice to Have
- [ ] Hub admin dashboard optimized for their workflow
- [ ] Permission checks comprehensive and consistent
- [ ] All edge cases handled gracefully

---

## Files to Modify

### Backend
- `models.py` - Add HUB_ADMIN role to enum
- `api/app/main.py` - Update permission guards throughout

### Frontend
- `frontend/src/pages/DashboardPage.vue` - Simplify and reorganize
- `frontend/src/pages/SurveyResponsesPage.vue` - Create new
- `frontend/src/pages/SettingsPage.vue` - Fix export function
- `frontend/src/layouts/MainLayout.vue` - Add menu item, update labels
- `frontend/src/router/routes.js` - Add survey responses route
- `frontend/src/router/index.js` - Add route guard for hub_admin
- `frontend/src/stores/auth.js` - Add hub_admin getters
- `frontend/src/pages/UsersPage.vue` - Update role labels
- `frontend/src/pages/UserDetailPage.vue` - Update role labels
- `frontend/src/pages/AccountsPage.vue` - Update role labels
- `frontend/src/pages/BatteriesPage.vue` - Add permission checks
- `frontend/src/pages/PUEPage.vue` - Add permission checks

### Testing
- `scripts/test_battery_submission.py` - Create new test script

### Database
- Create migration for HUB_ADMIN role documentation

---

## Notes

- Keep database role values lowercase: "user", "hub_admin", etc.
- Use display label mapping for UI presentation
- Backend is source of truth for permissions
- Frontend guards are UX enhancement, not security
- Test each role in isolated browser session to avoid cached auth
