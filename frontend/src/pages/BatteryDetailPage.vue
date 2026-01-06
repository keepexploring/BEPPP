<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <q-btn flat round dense icon="arrow_back" @click="$router.back()" />
        <span class="text-h4 q-ml-md">Battery {{ battery?.short_id || battery?.battery_id || 'Details' }}</span>
      </div>
      <div class="col-auto q-gutter-sm">
        <q-btn
          v-if="authStore.isAdmin && battery"
          label="Reset Secret"
          icon="vpn_key"
          color="secondary"
          outline
          @click="showSecretDialog = true"
        />
        <q-btn
          v-if="authStore.isAdmin && battery"
          label="Edit"
          icon="edit"
          color="warning"
          @click="editBattery"
        />
      </div>
    </div>

    <div v-if="loading" class="flex flex-center q-pa-xl">
      <q-spinner-gears size="50px" color="primary" />
    </div>

    <div v-else-if="battery" class="row q-col-gutter-md">
      <!-- Battery Info -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Battery Information</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <div><strong>Battery ID:</strong> {{ battery.battery_id }}</div>
            <div v-if="battery.short_id"><strong>Short ID:</strong> {{ battery.short_id }}</div>
            <div><strong>Capacity:</strong> {{ battery.battery_capacity_wh }}Wh</div>
            <div>
              <strong>Status:</strong>
              <q-badge :color="getStatusColor(battery.status)" class="q-ml-sm">
                {{ battery.status }}
              </q-badge>
              <q-btn
                v-if="battery.status === 'rented' && activeRental"
                flat
                dense
                size="sm"
                icon="open_in_new"
                color="primary"
                class="q-ml-sm"
                :to="{ name: 'rental-detail', params: { id: activeRental.rentral_id } }"
              >
                <q-tooltip>View Active Rental</q-tooltip>
              </q-btn>
            </div>
            <div v-if="battery.condition">
              <strong>Condition:</strong> {{ battery.condition }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Latest Data -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Latest Data</div>
              </div>
              <div class="col-auto">
                <q-btn
                  flat
                  round
                  dense
                  icon="refresh"
                  @click="loadLatestData"
                  :loading="loadingData"
                />
              </div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div v-if="latestData" class="q-gutter-sm">
              <div v-if="latestData.battery_voltage">
                <strong>Voltage:</strong> {{ latestData.battery_voltage }}V
              </div>
              <div v-if="latestData.battery_current">
                <strong>Current:</strong> {{ latestData.battery_current }}A
              </div>
              <div v-if="latestData.state_of_charge">
                <strong>State of Charge:</strong> {{ latestData.state_of_charge }}%
              </div>
              <div v-if="latestData.temperature">
                <strong>Temperature:</strong> {{ latestData.temperature }}°C
              </div>

              <!-- Timestamp Information -->
              <div v-if="latestData.timestamp || battery.last_data_received" class="q-mt-md q-pt-md" style="border-top: 1px solid #e0e0e0">
                <div class="text-subtitle2 text-grey-8 q-mb-xs">Timestamps</div>
                <div v-if="latestData.timestamp" class="q-ml-sm">
                  <strong>Battery Reported:</strong> {{ formatDate(latestData.timestamp) }}
                  <q-icon name="info" size="xs" color="grey-6" class="q-ml-xs">
                    <q-tooltip>Time from battery's internal clock (may be incorrect if RTC not set)</q-tooltip>
                  </q-icon>
                </div>
                <div v-if="battery.last_data_received" class="q-ml-sm">
                  <strong>Server Received:</strong> {{ formatDate(battery.last_data_received) }}
                  <q-icon name="info" size="xs" color="grey-6" class="q-ml-xs">
                    <q-tooltip>Time when server received this data (accurate)</q-tooltip>
                  </q-icon>
                </div>
                <div v-if="latestData.timestamp && battery.last_data_received && getTimestampDifference(latestData.timestamp, battery.last_data_received) > 60" class="q-ml-sm text-warning q-mt-xs">
                  <q-icon name="warning" size="xs" />
                  Time difference: {{ formatTimeDifference(latestData.timestamp, battery.last_data_received) }}
                  <q-tooltip>Battery clock may need adjustment</q-tooltip>
                </div>
              </div>

              <div v-if="latestData.error_message" class="text-negative">
                <strong>Error:</strong> {{ latestData.error_message }}
              </div>
            </div>
            <div v-else class="text-center text-grey-7">
              No data available
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Rental History -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Rental History</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list v-if="rentalHistory.length > 0" separator>
              <q-item
                v-for="rental in rentalHistory"
                :key="rental.rentral_id"
                clickable
                :to="{ name: 'rental-detail', params: { id: rental.rentral_id } }"
              >
                <q-item-section>
                  <q-item-label>
                    {{ rental.user_name }}
                    <q-badge :color="getRentalStatusColor(rental.status)" class="q-ml-sm">
                      {{ rental.status }}
                    </q-badge>
                  </q-item-label>
                  <q-item-label caption>
                    {{ formatDate(rental.timestamp_taken) }} -
                    {{ rental.battery_returned_date ? formatDate(rental.battery_returned_date) : 'Not returned' }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-icon name="chevron_right" />
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No rental history
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Notes & Maintenance -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Notes & Maintenance</div>
              </div>
              <div class="col-auto">
                <q-btn
                  v-if="authStore.isAdmin"
                  flat
                  round
                  dense
                  icon="add"
                  color="primary"
                  @click="showAddNoteDialog = true"
                >
                  <q-tooltip>Add Note</q-tooltip>
                </q-btn>
              </div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section style="max-height: 400px; overflow-y: auto;">
            <q-list v-if="notes.length > 0" separator>
              <q-item v-for="note in notes" :key="note.id">
                <q-item-section>
                  <q-item-label>{{ note.content }}</q-item-label>
                  <q-item-label caption>
                    {{ formatDate(note.created_at) }}
                    <span v-if="note.creator"> - {{ note.creator.Name || note.creator.username }}</span>
                  </q-item-label>
                </q-item-section>
                <q-item-section side top v-if="authStore.isAdmin">
                  <q-btn
                    flat
                    round
                    dense
                    size="sm"
                    icon="notifications"
                    color="warning"
                    @click="createNotificationFromNote(note)"
                  >
                    <q-tooltip>Create Notification</q-tooltip>
                  </q-btn>
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No notes yet
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Error History -->
      <div class="col-12">
        <ErrorHistoryTable :battery-id="batteryId" />
      </div>

      <!-- Historical Data Chart Placeholder -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Historical Data</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div class="text-center text-grey-7 q-pa-xl">
              <q-icon name="show_chart" size="64px" color="grey-5" />
              <div class="q-mt-md">
                Historical data visualization will be available in the Analytics dashboard
              </div>
              <q-btn
                label="View in Analytics"
                color="primary"
                class="q-mt-md"
                :to="{ name: 'analytics' }"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Battery Secret Dialog -->
    <q-dialog v-model="showSecretDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Reset Battery Secret</div>
        </q-card-section>

        <q-card-section>
          <div class="q-mb-md text-body2">
            Generate a new secret for battery {{ battery?.battery_id }} to access the API.
            The battery will need to use this new secret for authentication.
          </div>

          <q-input
            v-model="newSecret"
            label="New Secret"
            outlined
            :type="showSecret ? 'text' : 'password'"
            hint="Leave empty to auto-generate"
          >
            <template v-slot:append>
              <q-icon
                :name="showSecret ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="showSecret = !showSecret"
              />
              <q-icon
                name="refresh"
                class="cursor-pointer q-ml-sm"
                @click="generateSecret"
              >
                <q-tooltip>Generate Random Secret</q-tooltip>
              </q-icon>
            </template>
          </q-input>

          <div v-if="secretResetResult" class="q-mt-md q-pa-md bg-grey-2 rounded-borders">
            <div class="text-subtitle2 q-mb-sm">Connection Settings for Battery:</div>
            <div class="text-body2" style="word-break: break-all;">
              <strong>API URL:</strong> {{ window.location.origin }}/data<br>
              <strong>Battery ID:</strong> {{ battery?.battery_id }}<br>
              <strong>Secret:</strong> <span class="text-code">{{ secretResetResult.secret }}</span>
            </div>
            <q-btn
              flat
              dense
              icon="content_copy"
              label="Copy Settings"
              class="q-mt-sm"
              @click="copySettings"
            />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn label="Cancel" flat v-close-popup />
          <q-btn
            label="Reset Secret"
            color="primary"
            :loading="resettingSecret"
            @click="resetBatterySecret"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Add Note Dialog -->
    <q-dialog v-model="showAddNoteDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Add Note</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveNote" class="q-gutter-md">
            <q-input
              v-model="noteContent"
              label="Note"
              type="textarea"
              outlined
              rows="4"
              :rules="[val => !!val || 'Note content is required']"
              hint="Add maintenance notes, condition updates, or any other information"
            />

            <q-select
              v-model="noteCondition"
              :options="conditionOptions"
              label="Update Battery Condition (optional)"
              outlined
              clearable
              hint="Select if this note indicates a change in battery condition"
            />

            <q-checkbox
              v-model="createNotification"
              label="Create notification for this note"
            />

            <div class="row justify-end q-gutter-sm">
              <q-btn label="Cancel" flat v-close-popup />
              <q-btn
                label="Save"
                type="submit"
                color="primary"
                :loading="savingNote"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Edit Dialog -->
    <q-dialog v-model="showEditDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Edit Battery</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveBattery" class="q-gutter-md">
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
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { batteriesAPI, dataAPI, hubsAPI, batteryRentalsAPI, notificationsAPI } from 'src/services/api'
import { useQuasar, date, copyToClipboard } from 'quasar'
import { useAuthStore } from 'stores/auth'
import ErrorHistoryTable from 'src/components/ErrorHistoryTable.vue'

const $q = useQuasar()
const route = useRoute()
const authStore = useAuthStore()

const battery = ref(null)
const batteryId = computed(() => parseInt(route.params.id))
const latestData = ref(null)
const loading = ref(true)
const loadingData = ref(false)
const showEditDialog = ref(false)
const saving = ref(false)
const hubOptions = ref([])
const activeRental = ref(null)
const rentalHistory = ref([])
const notes = ref([])

// Secret reset
const showSecretDialog = ref(false)
const newSecret = ref('')
const showSecret = ref(false)
const resettingSecret = ref(false)
const secretResetResult = ref(null)

// Add note
const showAddNoteDialog = ref(false)
const noteContent = ref('')
const noteCondition = ref(null)
const createNotification = ref(false)
const savingNote = ref(false)

const formData = ref({
  hub_id: null,
  battery_capacity_wh: null,
  status: 'available'
})

const statusOptions = ['available', 'rented', 'maintenance', 'retired']
const conditionOptions = ['excellent', 'good', 'fair', 'poor', 'needs_repair']

const getStatusColor = (status) => {
  const colors = {
    available: 'positive',
    rented: 'warning',
    maintenance: 'info',
    retired: 'negative'
  }
  return colors[status] || 'grey'
}

const getRentalStatusColor = (status) => {
  const colors = {
    active: 'positive',
    overdue: 'negative',
    returned: 'grey'
  }
  return colors[status] || 'grey'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm:ss') + ' UTC'
}

const getTimestampDifference = (timestamp1, timestamp2) => {
  if (!timestamp1 || !timestamp2) return 0
  const date1 = new Date(timestamp1)
  const date2 = new Date(timestamp2)
  return Math.abs(date1 - date2) / 1000 // Return difference in seconds
}

const formatTimeDifference = (timestamp1, timestamp2) => {
  const diffSeconds = getTimestampDifference(timestamp1, timestamp2)

  if (diffSeconds < 60) {
    return `${Math.round(diffSeconds)} seconds`
  } else if (diffSeconds < 3600) {
    return `${Math.round(diffSeconds / 60)} minutes`
  } else if (diffSeconds < 86400) {
    return `${Math.round(diffSeconds / 3600)} hours`
  } else {
    return `${Math.round(diffSeconds / 86400)} days`
  }
}

const generateSecret = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  newSecret.value = result
}

const resetBatterySecret = async () => {
  resettingSecret.value = true
  try {
    const secret = newSecret.value || (() => {
      generateSecret()
      return newSecret.value
    })()

    await batteriesAPI.setBatterySecret(battery.value.battery_id, secret)

    secretResetResult.value = {
      secret,
      timestamp: new Date().toISOString()
    }

    $q.notify({
      type: 'positive',
      message: 'Battery secret reset successfully',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to reset battery secret',
      position: 'top'
    })
  } finally {
    resettingSecret.value = false
  }
}

const copySettings = () => {
  const settings = `API URL: ${window.location.origin}/data
Battery ID: ${battery.value.battery_id}
Secret: ${secretResetResult.value.secret}`

  copyToClipboard(settings)
    .then(() => {
      $q.notify({
        type: 'positive',
        message: 'Settings copied to clipboard',
        position: 'top'
      })
    })
    .catch(() => {
      $q.notify({
        type: 'negative',
        message: 'Failed to copy to clipboard',
        position: 'top'
      })
    })
}

const saveNote = async () => {
  savingNote.value = true
  try {
    // Create note via API
    const noteData = {
      content: noteContent.value,
      condition: noteCondition.value
    }

    await batteriesAPI.createNote(battery.value.battery_id, noteData)

    // Reload notes
    await loadNotes()

    // Create notification if requested
    if (createNotification.value) {
      await createNotificationFromNote({ content: noteContent.value })
    }

    $q.notify({
      type: 'positive',
      message: 'Note added successfully',
      position: 'top'
    })

    showAddNoteDialog.value = false
    noteContent.value = ''
    noteCondition.value = null
    createNotification.value = false
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to add note',
      position: 'top'
    })
  } finally {
    savingNote.value = false
  }
}

const createNotificationFromNote = async (note) => {
  try {
    const notificationData = {
      message: `Battery ${battery.value.battery_id}: ${note.content}`,
      notification_type: 'maintenance',
      severity: 'warning',
      link_type: 'battery',
      link_id: battery.value.battery_id
    }

    await notificationsAPI.create(notificationData)

    $q.notify({
      type: 'positive',
      message: 'Notification created',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create notification',
      position: 'top'
    })
  }
}

const loadNotes = async () => {
  try {
    const response = await batteriesAPI.getNotes(battery.value.battery_id)
    notes.value = response.data.notes || []
  } catch (error) {
    console.error('Failed to load notes:', error)
  }
}

const loadRentalHistory = async () => {
  try {
    const response = await batteryRentalsAPI.list({ battery_id: battery.value.battery_id })
    rentalHistory.value = response.data || []

    // Find active rental
    activeRental.value = rentalHistory.value.find(r =>
      r.status !== 'returned' && r.battery_id === battery.value.battery_id
    )
  } catch (error) {
    console.error('Failed to load rental history:', error)
  }
}

const loadBatteryDetails = async () => {
  loading.value = true

  try {
    const batteryId = route.params.id

    const response = await batteriesAPI.get(batteryId)
    battery.value = response.data

    await Promise.all([
      loadLatestData(),
      loadRentalHistory(),
      loadNotes()
    ])
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load battery details',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const loadLatestData = async () => {
  loadingData.value = true

  try {
    const batteryId = route.params.id
    const response = await dataAPI.getLatest(batteryId)
    latestData.value = response.data
  } catch (error) {
    console.error('Failed to load latest data:', error)
  } finally {
    loadingData.value = false
  }
}

const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

const editBattery = () => {
  formData.value = {
    hub_id: battery.value.hub_id,
    battery_capacity_wh: battery.value.battery_capacity_wh,
    status: battery.value.status
  }
  showEditDialog.value = true
}

const saveBattery = async () => {
  saving.value = true
  try {
    await batteriesAPI.update(battery.value.battery_id, formData.value)
    $q.notify({
      type: 'positive',
      message: 'Battery updated successfully',
      position: 'top'
    })
    showEditDialog.value = false

    // Reload battery details
    const response = await batteriesAPI.get(battery.value.battery_id)
    battery.value = response.data

    // Update formData with new values
    formData.value = {
      hub_id: battery.value.hub_id,
      battery_capacity_wh: battery.value.battery_capacity_wh,
      status: battery.value.status
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to update battery',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadBatteryDetails()
  loadHubs()
})
</script>
