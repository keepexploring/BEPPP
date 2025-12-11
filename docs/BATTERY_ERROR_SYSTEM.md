# Battery Error Tracking System

**Status**: 🟡 Partially Complete (Backend done, Frontend pending)
**Date**: December 11, 2025

---

## Overview

The battery error tracking system monitors and reports hardware errors from battery IoT devices. It features smart notifications that prevent flooding while ensuring users are alerted to critical issues.

---

## 🎯 Components

### 1. Error Codes

Battery devices report errors using single-character codes in the `err` field:

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| R | rtcError | Real-time clock error | warning |
| C | powerSensorChargeError | Power sensor charge error | error |
| U | powerSensorUsbError | Power sensor USB error | warning |
| T | tempSensorError | Temperature sensor error | warning |
| B | batteryMonitorError | Battery monitor error | error |
| G | gpsError | GPS error | warning |
| S | sdError | SD card error | warning |
| L | lteError | LTE connection error | error |
| D | displayError | Display error | info |

**Example**: `err: "TG"` means temperature sensor error + GPS error

---

## ✅ Completed Features

### Database Schema

The `livedata` table includes the `err` column:
```sql
err VARCHAR(255) NULL  -- Stores error codes from battery
```

**Migration**: `alembic/versions/0c9a1f2202d4_add_error_message_field_to_live_data.py`

### Webhook Processing

The webhook endpoint (`/webhook/live-data`) now:
1. Accepts the `err` field in battery data
2. Stores it in the database
3. Calls `process_battery_errors()` to create smart notifications

**Location**: `api/app/main.py:935-942`

### Smart Notification System

**Features**:
- Decodes error strings into human-readable messages
- Creates notifications for new errors only (prevents flooding)
- Tracks which errors have active notifications per battery
- Only creates new notification if old one was dismissed and error persists

**Functions**:
- `decode_error_string()` - api/app/main.py:813-829
- `process_battery_errors()` - api/app/main.py:831-906
- `BATTERY_ERROR_CODES` - api/app/main.py:800-811

**How it works**:
```python
# When battery submits data with err="TG"
process_battery_errors(db, battery_id=1, error_string="TG", hub_id=1)

# System checks for existing unread notifications:
# - If notification for error "T" exists and is unread: Skip (no flooding)
# - If no notification or was dismissed: Create new notification

# Result:
# - Notification 1: "Battery #1: Temperature sensor error"
# - Notification 2: "Battery #1: GPS error"
```

### Deployment Scripts

**Migration Fix Script**: `scripts/fix_livedata_err_column.sh`
- Checks if `err` column exists
- Adds it if missing
- Works in both local and production environments
- Usage: `bash scripts/fix_livedata_err_column.sh`

**Webhook Test Script**: `scripts/test_webhook_live_data.sh`
- Sends sample battery data with error codes
- Tests webhook processing
- Verifies data storage
- Usage: `bash scripts/test_webhook_live_data.sh [endpoint]`

**Deploy Script Updates**: `deploy.sh:466-494`
- Runs Alembic migrations automatically
- Verifies critical columns exist
- Provides helpful error messages if issues occur

---

## 🚧 Pending Implementation

### 1. API Endpoint for Battery Errors

**Endpoint**: `GET /batteries/{battery_id}/errors`

**Purpose**: Fetch error history for a specific battery

**Request**:
```bash
GET /batteries/1/errors?limit=50&time_period=last_week
Authorization: Bearer {token}
```

**Response**:
```json
{
  "battery_id": 1,
  "battery_name": "Battery #1",
  "errors": [
    {
      "id": 12345,
      "timestamp": "2025-12-11T10:24:41Z",
      "error_codes": "TG",
      "decoded_errors": [
        {
          "code": "T",
          "name": "tempSensorError",
          "description": "Temperature sensor error",
          "severity": "warning"
        },
        {
          "code": "G",
          "name": "gpsError",
          "description": "GPS error",
          "severity": "warning"
        }
      ],
      "other_metrics": {
        "soc": 97.1,
        "voltage": 13.285,
        "temperature": 14.625
      }
    }
  ],
  "total_errors": 42,
  "time_period": "last_week"
}
```

**Implementation Location**: Add to `api/app/main.py` after line 2530

**Code Template**:
```python
@app.get("/batteries/{battery_id}/errors", tags=["Batteries"])
async def get_battery_errors(
    battery_id: int,
    limit: int = 50,
    time_period: str = "last_week",  # last_24_hours, last_week, last_month
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get error history for a battery"""

    # Check battery exists and user has access
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")

    # Check access
    if current_user.get('role') not in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Calculate time range
    start_time, end_time = calculate_time_period(time_period)

    # Query live data with errors
    error_records = db.query(LiveData).filter(
        LiveData.battery_id == battery_id,
        LiveData.err.isnot(None),
        LiveData.err != '',
        LiveData.timestamp >= start_time,
        LiveData.timestamp <= end_time
    ).order_by(LiveData.timestamp.desc()).limit(limit).all()

    # Format response
    errors = []
    for record in error_records:
        decoded = decode_error_string(record.err) if record.err else []
        errors.append({
            "id": record.id,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "error_codes": record.err,
            "decoded_errors": decoded,
            "other_metrics": {
                "soc": record.state_of_charge,
                "voltage": record.voltage,
                "temperature": record.temp_battery,
                "power": record.power_watts
            }
        })

    return {
        "battery_id": battery_id,
        "battery_name": battery.battery_name,
        "errors": errors,
        "total_errors": len(errors),
        "time_period": time_period
    }
```

### 2. Frontend Error Display Table

**Location**: `frontend/src/pages/BatteryDetailPage.vue`

**Component**: Add new "Errors" tab or section

**Features**:
- Display error history in sortable table
- Show decoded error descriptions with severity badges
- Filter by time period
- Link to specific data points
- Show metrics at time of error

**UI Mockup**:
```
┌────────────────────────────────────────────────────────────┐
│ Battery #1 Details                                         │
├────────────────────────────────────────────────────────────┤
│ [Overview] [Live Data] [Errors] [Rentals] [Notes]         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Error History                          [Last Week ▼]      │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ Time          │ Errors                  │ Metrics    │  │
│ ├──────────────────────────────────────────────────────┤  │
│ │ 10:24 AM      │ ⚠️ Temp Sensor Error    │ SOC: 97%   │  │
│ │ Dec 11        │ ⚠️ GPS Error            │ V: 13.3V   │  │
│ ├──────────────────────────────────────────────────────┤  │
│ │ 09:15 AM      │ 🔴 Battery Monitor      │ SOC: 85%   │  │
│ │ Dec 11        │    Error                │ V: 12.1V   │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                            │
│ 42 errors in last week                                    │
└────────────────────────────────────────────────────────────┘
```

**Implementation Steps**:

1. **Add API call** to `frontend/src/services/api.js`:
```javascript
export async function getBatteryErrors(batteryId, timePeriod = 'last_week', limit = 50) {
  const response = await apiClient.get(
    `/batteries/${batteryId}/errors`,
    { params: { time_period: timePeriod, limit } }
  );
  return response.data;
}
```

2. **Create ErrorHistoryTable.vue component** in `frontend/src/components/`:
```vue
<template>
  <q-card>
    <q-card-section>
      <div class="row items-center justify-between">
        <div class="text-h6">Error History</div>
        <q-select
          v-model="timePeriod"
          :options="timeOptions"
          dense
          outlined
          @update:model-value="loadErrors"
        />
      </div>
    </q-card-section>

    <q-card-section>
      <q-table
        :rows="errors"
        :columns="columns"
        row-key="id"
        :loading="loading"
        flat
      >
        <template v-slot:body-cell-errors="props">
          <q-td :props="props">
            <div v-for="error in props.row.decoded_errors" :key="error.code">
              <q-badge
                :color="getSeverityColor(error.severity)"
                :label="error.description"
              />
            </div>
          </q-td>
        </template>
      </q-table>
    </q-card-section>
  </q-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getBatteryErrors } from '../services/api';

const props = defineProps({
  batteryId: {
    type: Number,
    required: true
  }
});

const errors = ref([]);
const loading = ref(false);
const timePeriod = ref('last_week');

const timeOptions = [
  { label: 'Last 24 Hours', value: 'last_24_hours' },
  { label: 'Last Week', value: 'last_week' },
  { label: 'Last Month', value: 'last_month' }
];

const columns = [
  {
    name: 'timestamp',
    label: 'Time',
    field: 'timestamp',
    sortable: true,
    format: (val) => new Date(val).toLocaleString()
  },
  {
    name: 'errors',
    label: 'Errors',
    field: 'decoded_errors',
    sortable: false
  },
  {
    name: 'metrics',
    label: 'Metrics',
    field: 'other_metrics',
    format: (val) => `SOC: ${val.soc}% | V: ${val.voltage}V`
  }
];

function getSeverityColor(severity) {
  switch (severity) {
    case 'error': return 'negative';
    case 'warning': return 'warning';
    case 'info': return 'info';
    default: return 'grey';
  }
}

async function loadErrors() {
  loading.value = true;
  try {
    const data = await getBatteryErrors(props.batteryId, timePeriod.value);
    errors.value = data.errors;
  } catch (error) {
    console.error('Failed to load battery errors:', error);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadErrors();
});
</script>
```

3. **Add to BatteryDetailPage.vue**:
```vue
<template>
  <q-page padding>
    <!-- Existing tabs -->
    <q-tabs v-model="tab">
      <q-tab name="overview" label="Overview" />
      <q-tab name="live" label="Live Data" />
      <q-tab name="errors" label="Errors" />  <!-- NEW -->
      <q-tab name="rentals" label="Rentals" />
      <q-tab name="notes" label="Notes" />
    </q-tabs>

    <q-tab-panels v-model="tab">
      <!-- Existing panels -->

      <!-- NEW Error History Panel -->
      <q-tab-panel name="errors">
        <ErrorHistoryTable :battery-id="batteryId" />
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup>
import ErrorHistoryTable from '../components/ErrorHistoryTable.vue';
// ...existing code
</script>
```

---

## 🧪 Testing

### Test Error Notifications

1. **Fix database schema** (if needed):
```bash
bash scripts/fix_livedata_err_column.sh
```

2. **Send test data with errors**:
```bash
bash scripts/test_webhook_live_data.sh
```

3. **Check notifications were created**:
```bash
# Via API
curl -X GET http://localhost:8000/notifications \
  -H "Authorization: Bearer {token}"

# Via database
docker exec battery-hub-db psql -U beppp -d beppp \
  -c "SELECT * FROM notifications WHERE notification_type LIKE 'battery_error_%' ORDER BY created_at DESC LIMIT 5;"
```

4. **Test no-flooding logic**:
```bash
# Send same error twice
bash scripts/test_webhook_live_data.sh
bash scripts/test_webhook_live_data.sh

# Should only create 2 notifications (T and G), not 4
```

5. **Test re-notification after dismissal**:
```bash
# Mark notification as read
curl -X PUT http://localhost:8000/notifications/{id}/read \
  -H "Authorization: Bearer {token}"

# Send error again
bash scripts/test_webhook_live_data.sh

# Should create new notification since old one was dismissed
```

### Test Error Endpoint (after implementation)

```bash
# Get errors for battery 1
curl -X GET "http://localhost:8000/batteries/1/errors?time_period=last_week&limit=50" \
  -H "Authorization: Bearer {token}"
```

---

## 📊 Database Queries

### View all errors for a battery

```sql
SELECT
  id,
  timestamp,
  err as error_codes,
  state_of_charge as soc,
  voltage,
  temp_battery as temperature
FROM livedata
WHERE battery_id = 1
  AND err IS NOT NULL
  AND err != ''
ORDER BY timestamp DESC
LIMIT 50;
```

### Count errors by type (last 7 days)

```sql
SELECT
  SUBSTRING(err, i, 1) as error_code,
  COUNT(*) as occurrences
FROM livedata,
  generate_series(1, LENGTH(err)) as i
WHERE battery_id = 1
  AND err IS NOT NULL
  AND err != ''
  AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY error_code
ORDER BY occurrences DESC;
```

### Find batteries with recent errors

```sql
SELECT
  b.battery_id,
  b.battery_name,
  COUNT(DISTINCT l.id) as error_count,
  MAX(l.timestamp) as last_error
FROM bepppbattery b
JOIN livedata l ON b.battery_id = l.battery_id
WHERE l.err IS NOT NULL
  AND l.err != ''
  AND l.timestamp > NOW() - INTERVAL '24 hours'
GROUP BY b.battery_id, b.battery_name
ORDER BY error_count DESC;
```

---

## 🚀 Production Deployment

The system is production-ready with these steps:

1. **Deploy code**:
```bash
sudo bash deploy.sh
# Automatically runs migrations and verifies err column exists
```

2. **Verify migration**:
```bash
docker exec battery-hub-db psql -U beppp -d beppp -c "\d livedata" | grep err
# Should show: err | character varying(255) |
```

3. **Test webhook**:
```bash
bash scripts/test_webhook_live_data.sh https://your-domain.com
```

4. **Monitor notifications**:
```bash
docker exec battery-hub-db psql -U beppp -d beppp \
  -c "SELECT COUNT(*) FROM notifications WHERE notification_type LIKE 'battery_error_%';"
```

---

## 📁 File Reference

### Modified Files
- `api/app/main.py:800-906` - Error processing functions
- `api/app/main.py:935-942` - Webhook integration
- `deploy.sh:466-494` - Migration automation
- `models.py:202` - err column definition
- `alembic/versions/0c9a1f2202d4_add_error_message_field_to_live_data.py` - Migration

### New Files
- `scripts/fix_livedata_err_column.sh` - Column fix script
- `scripts/test_webhook_live_data.sh` - Webhook test script
- `docs/BATTERY_ERROR_SYSTEM.md` - This document

### Pending Files (to create)
- Endpoint in `api/app/main.py` (~50 lines)
- `frontend/src/components/ErrorHistoryTable.vue` (~150 lines)
- Updates to `frontend/src/pages/BatteryDetailPage.vue` (~10 lines)
- Updates to `frontend/src/services/api.js` (~8 lines)

---

## ✨ Summary

**Completed** (Backend):
- ✅ Database schema with err column
- ✅ Webhook processing and storage
- ✅ Smart notification system (no flooding)
- ✅ Error code decoding
- ✅ Migration scripts
- ✅ Test scripts
- ✅ Deployment automation

**Pending** (Frontend):
- ⏳ API endpoint for fetching errors
- ⏳ Error history table component
- ⏳ Integration into battery detail page

**Estimated Time to Complete**: 1-2 hours for frontend implementation

**The backend is fully functional and ready for production use!**
