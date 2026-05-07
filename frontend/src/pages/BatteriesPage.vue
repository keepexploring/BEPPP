<template>
  <q-page class="q-pa-md">
    <q-banner v-if="isOffline" class="bg-orange text-white q-mb-md" rounded>
      <template v-slot:avatar>
        <q-icon name="cloud_off" />
      </template>
      You are offline. Showing cached data.
    </q-banner>

    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="col-12 col-sm-auto">
        <div class="text-h5">Batteries</div>
      </div>
      <div class="col-12 col-sm row items-center q-gutter-sm">
        <HubFilter v-model="selectedHub" @change="onHubChange" />
        <q-btn
          v-if="authStore.isAdmin"
          label="Add Battery"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
          size="sm"
          class="col-12 col-sm-auto"
        />
        <q-space />
        <q-toggle
          v-model="autoRefresh"
          label="Auto-refresh"
          color="primary"
          @update:model-value="toggleAutoRefresh"
          dense
        />
        <q-select
          v-if="autoRefresh"
          v-model="refreshInterval"
          :options="refreshIntervalOptions"
          label="Interval"
          outlined
          dense
          emit-value
          map-options
          style="min-width: 110px"
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

    <q-card>
      <q-card-section>
        <q-table
          :rows="batteries"
          :columns="columns"
          row-key="battery_id"
          :loading="loading"
          :filter="filter"
          :pagination="pagination"
          @row-click="(_evt, row) => $router.push({ name: 'battery-detail', params: { id: row.battery_id } })"
          class="cursor-pointer"
          :no-data-label="selectedHub ? 'No batteries found for this hub - add one to get started!' : 'No batteries available yet - add your first battery!'"
        >
          <template v-slot:top-right>
            <q-input
              v-model="filter"
              outlined
              dense
              debounce="300"
              placeholder="Search"
            >
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </template>

          <template v-slot:body-cell-data_status="props">
            <q-td :props="props">
              <q-icon
                name="circle"
                :color="getBatteryDataStatusColor(props.row.last_data_received)"
                size="sm"
              >
                <q-tooltip>
                  {{ props.row.last_data_received
                    ? `Last data: ${new Date(props.row.last_data_received).toLocaleString()} ${currentTimezone}`
                    : 'No data received yet'
                  }}
                </q-tooltip>
              </q-icon>
            </q-td>
          </template>

          <template v-slot:body-cell-last_data_received="props">
            <q-td :props="props">
              <span v-if="props.row.last_data_received">
                {{ formatRelativeTime(props.row.last_data_received) }}
                <q-tooltip>
                  {{ new Date(props.row.last_data_received).toLocaleString() }} {{ currentTimezone }}
                </q-tooltip>
              </span>
              <span v-else class="text-grey">Never</span>
            </q-td>
          </template>

          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-badge
                :color="getStatusColor(props.row.status)"
                :label="props.row.status"
              />
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
                :to="{ name: 'battery-detail', params: { id: props.row.battery_id } }"
              />
              <q-btn
                v-if="authStore.isAdmin"
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click="editBattery(props.row)"
              />
              <q-btn
                v-if="authStore.isSuperAdmin"
                flat
                round
                dense
                icon="delete"
                color="negative"
                @click="deleteBattery(props.row)"
              />
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Create/Edit Dialog -->
    <q-dialog v-model="showCreateDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">{{ editingBattery ? 'Edit Battery' : 'Create Battery' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveBattery" class="q-gutter-md">
            <q-input
              v-if="!editingBattery"
              v-model="formData.battery_id"
              label="Battery ID"
              type="text"
              outlined
              :rules="[val => !!val || 'Battery ID is required']"
              hint="Unique identifier (e.g., BAT-001, B-123-ABC)"
            />

            <q-select
              v-model="formData.hub_id"
              :options="hubOptions"
              option-value="hub_id"
              option-label="what_three_word_location"
              emit-value
              map-options
              label="Hub"
              outlined
              :rules="[val => !!val || 'Hub is required']"
            />

            <q-input
              v-model.number="formData.battery_capacity_wh"
              label="Battery Capacity (Wh)"
              type="number"
              outlined
              hint="Battery capacity in watt-hours"
            />

            <q-select
              v-model="formData.status"
              :options="statusOptions"
              label="Status"
              outlined
            />

            <div v-if="authStore.isAdmin && !editingBattery" class="q-gutter-sm">
              <q-input
                v-model="formData.battery_secret"
                label="Battery Secret (for API access)"
                type="password"
                outlined
                hint="Optional: Set a secret for this battery to access the API"
              />
            </div>

            <div class="row justify-end q-gutter-sm">
              <q-btn label="Cancel" flat v-close-popup />
              <q-btn
                label="Save"
                type="submit"
                color="primary"
                :loading="saving"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, inject, onMounted, onUnmounted, computed, watch } from 'vue'
import { batteriesAPI, hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useQuasar } from 'quasar'
import HubFilter from 'src/components/HubFilter.vue'

const $q = useQuasar()
const authStore = useAuthStore()
const hubSettingsStore = useHubSettingsStore()
const networkState = inject('networkState', { online: ref(true) })
const isOffline = computed(() => !networkState.online.value)
const selectedHub = ref(null)
const currentTimezone = computed(() => hubSettingsStore.currentTimezone || 'UTC')

const batteries = ref([])
const hubOptions = ref([])
const loading = ref(false)
const filter = ref('')
const showCreateDialog = ref(false)
const editingBattery = ref(null)
const saving = ref(false)

// Pagination settings
const pagination = ref({
  sortBy: 'battery_id',
  descending: false,
  page: 1,
  rowsPerPage: hubSettingsStore.currentTableRowsPerPage
})

const formData = ref({
  battery_id: null,
  hub_id: null,
  battery_capacity_wh: null,
  status: 'available',
  battery_secret: ''
})

const statusOptions = ['available', 'rented', 'maintenance', 'retired']

// Auto-refresh state
const autoRefresh = ref(false)
const refreshInterval = ref(30)
const refreshIntervalOptions = [
  { label: '10 seconds', value: 10 },
  { label: '30 seconds', value: 30 },
  { label: '60 seconds', value: 60 },
  { label: '5 minutes', value: 300 }
]
const timeUntilRefresh = ref(0)
let refreshTimer = null
let countdownTimer = null

const toggleAutoRefresh = (enabled) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  stopAutoRefresh()
  const intervalValue = typeof refreshInterval.value === 'object' && refreshInterval.value
    ? refreshInterval.value.value
    : refreshInterval.value || 30
  const intervalMs = intervalValue * 1000
  timeUntilRefresh.value = intervalValue

  countdownTimer = setInterval(() => {
    timeUntilRefresh.value -= 1
    if (timeUntilRefresh.value <= 0) {
      timeUntilRefresh.value = intervalValue
    }
  }, 1000)

  refreshTimer = setInterval(() => {
    loadBatteries()
  }, intervalMs)
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

const formatRelativeTime = (dateStr) => {
  if (!dateStr) return 'Never'
  const now = new Date()
  const date = new Date(dateStr)
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

const columns = computed(() => {
  const cols = [
    {
      name: 'battery_id',
      label: 'ID',
      field: 'battery_id',
      align: 'left',
      sortable: true,
      sort: (a, b) => {
        // Extract numbers from IDs for numeric sorting (e.g., "5" before "10", "BAT-2" before "BAT-10")
        const numA = parseInt((a || '').replace(/\D/g, '')) || 0
        const numB = parseInt((b || '').replace(/\D/g, '')) || 0
        if (numA !== numB) return numA - numB
        return String(a || '').localeCompare(String(b || ''))
      }
    }
  ]

  // Add hub column for superadmins
  if (authStore.isSuperAdmin) {
    cols.push({
      name: 'hub',
      label: 'Hub',
      field: row => {
        const hub = hubOptions.value.find(h => h.hub_id === row.hub_id)
        return hub ? hub.what_three_word_location : `Hub ${row.hub_id}`
      },
      align: 'left',
      sortable: true
    })
  }

  cols.push(
    { name: 'data_status', label: 'Data', field: 'last_data_received', align: 'center', sortable: true },
    {
      name: 'last_data_received',
      label: 'Last Data Sent',
      field: 'last_data_received',
      align: 'left',
      sortable: true,
      format: val => val ? formatRelativeTime(val) : 'Never'
    },
    { name: 'battery_capacity_wh', label: 'Capacity (Wh)', field: 'battery_capacity_wh', align: 'left', sortable: true },
    { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
    { name: 'actions', label: 'Actions', align: 'center' }
  )

  return cols
})

// Calculate battery data status color based on last_data_received
const getBatteryDataStatusColor = (lastDataReceived) => {
  if (!lastDataReceived) return 'grey'

  const now = new Date()
  const lastReceived = new Date(lastDataReceived)
  const hoursSinceData = (now - lastReceived) / (1000 * 60 * 60)

  const greenThreshold = hubSettingsStore.currentHubSettings?.battery_status_green_hours || 3
  const orangeThreshold = hubSettingsStore.currentHubSettings?.battery_status_orange_hours || 8

  if (hoursSinceData <= greenThreshold) return 'positive'  // Green
  if (hoursSinceData <= orangeThreshold) return 'orange'   // Orange
  return 'negative'  // Red
}

const getStatusColor = (status) => {
  const colors = {
    available: 'positive',
    rented: 'warning',
    maintenance: 'info',
    retired: 'negative'
  }
  return colors[status] || 'grey'
}

const loadBatteries = async () => {
  loading.value = true
  try {
    if (selectedHub.value) {
      // Load batteries for selected hub only
      const batteriesResponse = await hubsAPI.getBatteries(selectedHub.value)
      batteries.value = batteriesResponse.data
    } else {
      // Load all hubs to get all batteries
      const hubsResponse = await hubsAPI.list()
      const allBatteries = []

      for (const hub of hubsResponse.data) {
        const batteriesResponse = await hubsAPI.getBatteries(hub.hub_id)
        allBatteries.push(...batteriesResponse.data)
      }

      batteries.value = allBatteries
    }
  } catch (error) {
    if (navigator.onLine) {
      $q.notify({
        type: 'negative',
        message: 'Failed to load batteries',
        position: 'top'
      })
    }
  } finally {
    loading.value = false
  }
}

const onHubChange = (hubId) => {
  selectedHub.value = hubId
  loadBatteries()
}

const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

const editBattery = (battery) => {
  editingBattery.value = battery
  formData.value = { ...battery }
  showCreateDialog.value = true
}

const saveBattery = async () => {
  saving.value = true
  try {
    if (editingBattery.value) {
      await batteriesAPI.update(editingBattery.value.battery_id, formData.value)
      $q.notify({
        type: 'positive',
        message: 'Battery updated successfully',
        position: 'top'
      })
    } else {
      const result = await batteriesAPI.create(formData.value)
      const queued = result.data?._offlineQueued
      if (queued) {
        // Add synthetic battery to local list immediately for offline UX
        batteries.value = [...batteries.value, result.data]
      }
      $q.notify({
        type: queued ? 'info' : 'positive',
        message: queued
          ? 'Battery creation queued for sync'
          : (result.data?.short_id
            ? `Battery created successfully! ID: ${result.data.short_id}`
            : 'Battery created successfully'),
        position: 'top',
        timeout: 5000
      })
    }
    showCreateDialog.value = false
    resetForm()
    loadBatteries()
  } catch (error) {
    if (!isOffline.value) {
      $q.notify({
        type: 'negative',
        message: error.response?.data?.detail || 'Failed to save battery',
        position: 'top'
      })
    }
  } finally {
    saving.value = false
  }
}

const deleteBattery = (battery) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Are you sure you want to delete battery ${battery.battery_id}?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await batteriesAPI.delete(battery.battery_id)
      $q.notify({
        type: 'positive',
        message: 'Battery deleted successfully',
        position: 'top'
      })
      loadBatteries()
    } catch (error) {
      if (!isOffline.value) {
        $q.notify({
          type: 'negative',
          message: 'Failed to delete battery',
          position: 'top'
        })
      }
    }
  })
}

const resetForm = () => {
  formData.value = {
    battery_id: null,
    hub_id: null,
    battery_capacity_wh: null,
    status: 'available',
    battery_secret: ''
  }
  editingBattery.value = null
}

// Listen for SWR background revalidation to swap in fresh battery data
const onCacheUpdated = (event) => {
  const { url, data } = event.detail || {}
  if (!url || !data) return

  if (url.includes('/batteries') && Array.isArray(data)) {
    if (data.length === 0 && batteries.value.length > 0) return
    if (selectedHub.value) {
      const hubBatteries = data.filter(b => b.hub_id === selectedHub.value)
      if (hubBatteries.length > 0) batteries.value = hubBatteries
    } else {
      const freshMap = new Map(data.map(b => [b.battery_id, b]))
      batteries.value = batteries.value.map(b => freshMap.get(b.battery_id) || b)
      for (const b of data) {
        if (!batteries.value.find(existing => existing.battery_id === b.battery_id)) {
          batteries.value.push(b)
        }
      }
    }
  }
}

onMounted(async () => {
  loadBatteries()
  loadHubs()
  window.addEventListener('cache-updated', onCacheUpdated)
})

// Restart auto-refresh when interval changes
watch(refreshInterval, () => {
  if (autoRefresh.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('cache-updated', onCacheUpdated)
})
</script>
