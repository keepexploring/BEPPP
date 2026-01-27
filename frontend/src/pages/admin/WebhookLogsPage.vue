<template>
  <q-page class="q-pa-md">
    <div class="text-h4 q-mb-md">Webhook Logs</div>

    <q-card>
      <q-card-section>
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-12 col-md-3">
            <q-select
              v-model="filters.battery_id"
              :options="batteryOptions"
              option-label="label"
              option-value="value"
              emit-value
              map-options
              label="Battery"
              outlined
              dense
              clearable
              use-input
              input-debounce="300"
              @filter="filterBatteries"
            >
              <template v-slot:no-option>
                <q-item>
                  <q-item-section class="text-grey">
                    No batteries found
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>
          <div class="col-12 col-md-3">
            <q-input
              v-model.number="filters.limit"
              label="Limit"
              type="number"
              outlined
              dense
              :min="1"
              :max="1000"
            />
          </div>
          <div class="col-12 col-md-3">
            <q-input
              v-model="filters.search"
              label="Search (endpoint, method, etc.)"
              outlined
              dense
              clearable
            >
              <template v-slot:prepend>
                <q-icon name="search" />
              </template>
            </q-input>
          </div>
          <div class="col-12 col-md-2">
            <q-btn
              label="Apply Filters"
              icon="filter_list"
              color="primary"
              @click="loadLogs"
              class="full-width"
            />
          </div>
          <div class="col-12 col-md-4">
            <div class="row q-gutter-sm">
              <q-toggle
                v-model="autoRefresh"
                label="Auto-refresh"
                color="primary"
                @update:model-value="toggleAutoRefresh"
              />
              <q-select
                v-model="refreshInterval"
                :options="refreshIntervalOptions"
                label="Interval"
                outlined
                dense
                style="min-width: 100px"
                :disable="!autoRefresh"
              />
              <q-chip
                v-if="autoRefresh && timeUntilRefresh > 0"
                color="primary"
                text-color="white"
                icon="schedule"
                size="sm"
              >
                {{ timeUntilRefresh }}s
              </q-chip>
            </div>
          </div>
        </div>

        <q-table
          :rows="logs"
          :columns="columns"
          row-key="log_id"
          :loading="loading"
          :pagination="pagination"
        >
          <template v-slot:body-cell-battery_id="props">
            <q-td :props="props">
              {{ props.row.battery_id || 'N/A' }}
            </q-td>
          </template>

          <template v-slot:body-cell-status_code="props">
            <q-td :props="props">
              <q-badge
                :color="props.row.status_code >= 200 && props.row.status_code < 300 ? 'positive' : 'negative'"
                :label="props.row.status_code"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-timestamp="props">
            <q-td :props="props">
              {{ formatDate(props.row.timestamp) }}
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                dense
                icon="visibility"
                color="primary"
                @click="viewDetails(props.row)"
              />
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Details Dialog -->
    <q-dialog v-model="showDetailsDialog">
      <q-card style="min-width: 600px; max-width: 80vw">
        <q-card-section>
          <div class="text-h6">Webhook Details</div>
        </q-card-section>

        <q-separator />

        <q-card-section v-if="selectedLog" class="q-gutter-md">
          <div class="row q-col-gutter-sm">
            <div class="col-6"><strong>Log ID:</strong> {{ selectedLog.log_id }}</div>
            <div class="col-6"><strong>Battery ID:</strong> {{ selectedLog.battery_id }}</div>
            <div class="col-6"><strong>Endpoint:</strong> {{ selectedLog.endpoint }}</div>
            <div class="col-6"><strong>Method:</strong> {{ selectedLog.method }}</div>
            <div class="col-6"><strong>Status Code:</strong>
              <q-badge
                :color="selectedLog.status_code >= 200 && selectedLog.status_code < 300 ? 'positive' : 'negative'"
                :label="selectedLog.status_code"
              />
            </div>
            <div class="col-6"><strong>Timestamp:</strong> {{ formatDate(selectedLog.timestamp) }}</div>
          </div>

          <q-separator />

          <div v-if="selectedLog.request_headers">
            <div class="text-subtitle2">Request Headers:</div>
            <pre class="code-block">{{ formatJSON(selectedLog.request_headers) }}</pre>
          </div>

          <div v-if="selectedLog.request_body">
            <div class="text-subtitle2">Request Body:</div>
            <pre class="code-block">{{ formatJSON(selectedLog.request_body) }}</pre>
          </div>

          <q-separator />

          <div v-if="selectedLog.response_body">
            <div class="text-subtitle2">Response Body:</div>
            <pre class="code-block">{{ formatJSON(selectedLog.response_body) }}</pre>
          </div>

          <div v-if="selectedLog.error_message">
            <div class="text-subtitle2 text-negative">Error Message:</div>
            <div class="text-negative code-block">{{ selectedLog.error_message }}</div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn label="Close" flat v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { adminAPI, batteriesAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'
import { useHubSettingsStore } from 'stores/hubSettings'

const $q = useQuasar()
const hubSettingsStore = useHubSettingsStore()

const logs = ref([])
const batteries = ref([])
const batteryOptions = ref([])
const loading = ref(false)
const showDetailsDialog = ref(false)
const selectedLog = ref(null)

// Auto-refresh state
const autoRefresh = ref(false)
const refreshInterval = ref(10)
const refreshIntervalOptions = [
  { label: '5 seconds', value: 5 },
  { label: '10 seconds', value: 10 },
  { label: '30 seconds', value: 30 },
  { label: '60 seconds', value: 60 }
]
const timeUntilRefresh = ref(0)
let refreshTimer = null
let countdownTimer = null

const filters = ref({
  battery_id: null,
  search: '',
  limit: 100
})

const pagination = ref({
  rowsPerPage: 20
})

const columns = [
  { name: 'log_id', label: 'ID', field: 'log_id', align: 'left', sortable: true },
  { name: 'battery_id', label: 'Battery ID', field: 'battery_id', align: 'left', sortable: true },
  { name: 'endpoint', label: 'Endpoint', field: 'endpoint', align: 'left', sortable: true },
  { name: 'method', label: 'Method', field: 'method', align: 'left', sortable: true },
  { name: 'timestamp', label: 'Timestamp', field: 'timestamp', align: 'left', sortable: true },
  { name: 'status_code', label: 'Status', field: 'status_code', align: 'center', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const timezone = hubSettingsStore.currentTimezone || 'UTC'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm:ss') + ` ${timezone}`
}

const formatJSON = (data) => {
  if (!data) return '-'
  if (typeof data === 'string') {
    try {
      return JSON.stringify(JSON.parse(data), null, 2)
    } catch {
      return data
    }
  }
  return JSON.stringify(data, null, 2)
}

const loadBatteries = async () => {
  try {
    const response = await batteriesAPI.list()
    batteries.value = response.data || []

    // Create options for the dropdown
    batteryOptions.value = batteries.value.map(b => ({
      label: `${b.battery_id} - ${b.serial_number || 'N/A'}`,
      value: b.battery_id
    }))
  } catch (error) {
    console.error('Failed to load batteries:', error)
  }
}

const filterBatteries = (val, update) => {
  update(() => {
    if (val === '') {
      batteryOptions.value = batteries.value.map(b => ({
        label: `${b.battery_id} - ${b.serial_number || 'N/A'}`,
        value: b.battery_id
      }))
    } else {
      const needle = val.toLowerCase()
      batteryOptions.value = batteries.value
        .filter(b =>
          b.battery_id.toString().includes(needle) ||
          (b.serial_number && b.serial_number.toLowerCase().includes(needle))
        )
        .map(b => ({
          label: `${b.battery_id} - ${b.serial_number || 'N/A'}`,
          value: b.battery_id
        }))
    }
  })
}

const loadLogs = async () => {
  loading.value = true

  try {
    const params = {
      limit: filters.value.limit || 100
    }

    if (filters.value.battery_id) {
      params.battery_id = filters.value.battery_id
    }

    const response = await adminAPI.getWebhookLogs(params)
    // API returns { logs: [...], total_logs: N, showing: N, limit: N }
    let loadedLogs = response.data.logs || []

    // Client-side search filtering (since API doesn't support search yet)
    if (filters.value.search && filters.value.search.trim()) {
      const searchLower = filters.value.search.toLowerCase()
      loadedLogs = loadedLogs.filter(log =>
        log.endpoint?.toLowerCase().includes(searchLower) ||
        log.method?.toLowerCase().includes(searchLower) ||
        log.battery_id?.toString().includes(searchLower) ||
        log.request_body?.toLowerCase().includes(searchLower) ||
        log.response_body?.toLowerCase().includes(searchLower)
      )
    }

    logs.value = loadedLogs
  } catch (error) {
    console.error('Failed to load webhook logs:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to load webhook logs',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const viewDetails = (log) => {
  selectedLog.value = log
  showDetailsDialog.value = true
}

const toggleAutoRefresh = (enabled) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  stopAutoRefresh() // Clear any existing timers

  const interval = (refreshInterval.value?.value || refreshInterval.value || 10) * 1000
  timeUntilRefresh.value = interval / 1000

  // Countdown timer (updates every second)
  countdownTimer = setInterval(() => {
    timeUntilRefresh.value -= 1
    if (timeUntilRefresh.value <= 0) {
      timeUntilRefresh.value = interval / 1000
    }
  }, 1000)

  // Refresh timer (refreshes data at interval)
  refreshTimer = setInterval(() => {
    loadLogs()
  }, interval)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  timeUntilRefresh.value = 0
}

onMounted(() => {
  loadBatteries()
  loadLogs()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.code-block {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>
