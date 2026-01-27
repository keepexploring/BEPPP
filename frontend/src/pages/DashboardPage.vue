<template>
  <q-page class="q-pa-md">
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h4">Dashboard</div>
      <HubFilter v-if="authStore.isSuperAdmin" v-model="selectedHub" @change="onHubChange" />
    </div>

    <div class="row q-col-gutter-md">
      <!-- Quick Actions - AT TOP -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Quick Actions</div>
          </q-card-section>
          <q-card-section class="row q-col-gutter-md">
            <div class="col-12 col-sm-6 col-md-4 col-lg-2">
              <q-btn
                unelevated
                size="lg"
                class="full-width q-py-md"
                color="primary"
                @click="$router.push({ name: 'create-battery-rental' })"
              >
                <div class="column items-center q-gutter-xs">
                  <q-icon name="battery_charging_full" size="42px" />
                  <div class="text-weight-medium">Rent Battery</div>
                </div>
              </q-btn>
            </div>
            <div class="col-12 col-sm-6 col-md-4 col-lg-2">
              <q-btn
                unelevated
                size="lg"
                class="full-width q-py-md"
                color="purple"
                @click="$router.push({ name: 'create-pue-rental' })"
              >
                <div class="column items-center q-gutter-xs">
                  <q-icon name="power" size="42px" />
                  <div class="text-weight-medium">Rent PUE</div>
                </div>
              </q-btn>
            </div>
            <div class="col-12 col-sm-6 col-md-4 col-lg-2">
              <q-btn
                unelevated
                size="lg"
                class="full-width q-py-md"
                color="positive"
                @click="$router.push({ name: 'rentals', query: { action: 'returns' } })"
              >
                <div class="column items-center q-gutter-xs">
                  <q-icon name="assignment_return" size="42px" />
                  <div class="text-weight-medium">Returns</div>
                </div>
              </q-btn>
            </div>
            <div class="col-12 col-sm-6 col-md-4 col-lg-2">
              <q-btn
                outline
                size="lg"
                class="full-width q-py-md"
                color="primary"
                @click="$router.push({ name: 'rentals' })"
              >
                <div class="column items-center q-gutter-xs">
                  <q-icon name="format_list_bulleted" size="42px" />
                  <div class="text-weight-medium">View Rentals</div>
                </div>
              </q-btn>
            </div>
            <div class="col-12 col-sm-6 col-md-4 col-lg-2">
              <q-btn
                outline
                size="lg"
                class="full-width q-py-md"
                color="primary"
                @click="$router.push({ name: 'users' })"
              >
                <div class="column items-center q-gutter-xs">
                  <q-icon name="groups" size="42px" />
                  <div class="text-weight-medium">View Users</div>
                </div>
              </q-btn>
            </div>
            <div class="col-12 col-sm-6 col-md-4 col-lg-2">
              <q-btn
                unelevated
                size="lg"
                class="full-width q-py-md"
                color="secondary"
                @click="$router.push({ name: 'users', query: { action: 'create' } })"
              >
                <div class="column items-center q-gutter-xs">
                  <q-icon name="person_add" size="42px" />
                  <div class="text-weight-medium">Create User</div>
                </div>
              </q-btn>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Battery Status Cards -->
      <div class="col-12 col-md-4">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Batteries Available</div>
                <div class="text-h4">{{ stats.batteriesAvailable }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="battery_full" size="48px" color="positive" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">In Maintenance</div>
                <div class="text-h4">{{ stats.batteriesMaintenance }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="build" size="48px" color="warning" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Out for Rental</div>
                <div class="text-h4">{{ stats.batteriesRented }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="electric_bolt" size="48px" color="accent" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Battery List Display -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="row items-center justify-between">
              <div class="text-h6">Battery Status Overview</div>
              <div class="row q-gutter-sm">
                <q-input
                  v-model="batterySearchQuery"
                  outlined
                  dense
                  placeholder="Search by ID..."
                  style="min-width: 200px"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
                <q-select
                  v-model="batteryStatusFilter"
                  outlined
                  dense
                  :options="statusFilterOptions"
                  placeholder="Filter by status"
                  style="min-width: 150px"
                  clearable
                />
              </div>
            </div>
          </q-card-section>
          <q-card-section>
            <q-list separator bordered>
              <q-item
                v-for="battery in filteredBatteryList"
                :key="battery.battery_id"
                clickable
                @click="$router.push({ name: 'battery-detail', params: { id: battery.battery_id } })"
              >
                <q-item-section avatar>
                  <q-avatar :color="getBatteryStatusColor(battery.status)" text-color="white" :icon="getBatteryStatusIcon(battery.status)" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                    <strong>{{ battery.short_id || `Battery #${battery.battery_id}` }}</strong>
                    <q-badge :color="getBatteryStatusColor(battery.status)" class="q-ml-sm">
                      {{ formatBatteryStatus(battery.status) }}
                    </q-badge>
                  </q-item-label>
                  <q-item-label caption>
                    Location: {{ battery.hub_name || 'Unknown Hub' }}
                    <template v-if="battery.battery_capacity_wh">
                      | Capacity: {{ battery.battery_capacity_wh }}Wh
                    </template>
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="arrow_forward"
                    color="primary"
                    @click.stop="$router.push({ name: 'battery-detail', params: { id: battery.battery_id } })"
                  />
                </q-item-section>
              </q-item>
            </q-list>
            <div v-if="filteredBatteryList.length === 0" class="text-center text-grey-7 q-pa-md">
              <q-icon name="battery_unknown" size="48px" />
              <div class="q-mt-sm">No batteries found</div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Overdue & Upcoming Rentals -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">
              Rental Alerts
              <q-badge v-if="overdueCount > 0" color="negative" class="q-ml-sm">
                {{ overdueCount }} overdue
              </q-badge>
              <q-badge v-if="upcomingCount > 0" color="warning" class="q-ml-sm">
                {{ upcomingCount }} due soon
              </q-badge>
            </div>
          </q-card-section>

          <!-- Overdue Rentals -->
          <q-card-section v-if="overdueRentals.length > 0">
            <div class="text-subtitle2 text-negative q-mb-sm">Overdue Rentals</div>
            <q-list separator bordered>
              <q-item
                v-for="rental in overdueRentals"
                :key="rental.rentral_id"
                clickable
                @click="showRentalDetails(rental)"
              >
                <q-item-section avatar>
                  <q-avatar color="negative" text-color="white" icon="warning" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                    Battery {{ rental.battery_id }} - {{ rental.user_name }}
                    <q-badge color="negative" class="q-ml-sm">
                      {{ rental.days_overdue }}d overdue
                    </q-badge>
                  </q-item-label>
                  <q-item-label caption>
                    Hub: {{ rental.hub_name }} | User: {{ rental.username }}
                    <template v-if="rental.mobile_number"> | Mobile: {{ rental.mobile_number }}</template>
                  </q-item-label>
                  <q-item-label caption>
                    Due: {{ formatDate(rental.due_back) }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="visibility"
                    color="primary"
                    @click.stop="showRentalDetails(rental)"
                  />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>

          <!-- Upcoming Rentals -->
          <q-card-section v-if="upcomingRentals.length > 0">
            <div class="text-subtitle2 text-warning q-mb-sm">Due Soon (Next 3 Days)</div>
            <q-list separator bordered>
              <q-item
                v-for="rental in upcomingRentals"
                :key="rental.rentral_id"
                clickable
                @click="showRentalDetails(rental)"
              >
                <q-item-section avatar>
                  <q-avatar color="warning" text-color="white" icon="schedule" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                    Battery {{ rental.battery_id }} - {{ rental.user_name }}
                    <q-badge color="warning" class="q-ml-sm">
                      Due in {{ rental.days_until_due }}d
                    </q-badge>
                  </q-item-label>
                  <q-item-label caption>
                    Hub: {{ rental.hub_name }} | User: {{ rental.username }}
                    <template v-if="rental.mobile_number"> | Mobile: {{ rental.mobile_number }}</template>
                  </q-item-label>
                  <q-item-label caption>
                    Due: {{ formatDate(rental.due_back) }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="visibility"
                    color="primary"
                    @click.stop="showRentalDetails(rental)"
                  />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>

          <q-card-section v-if="overdueRentals.length === 0 && upcomingRentals.length === 0">
            <div class="text-center text-grey-7 q-pa-md">
              <q-icon name="check_circle" size="48px" color="positive" />
              <div class="q-mt-sm">All rentals are on schedule!</div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- PUE Inspection Alerts -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">
              PUE Inspection Alerts
              <q-badge v-if="overdueInspectionsCount > 0" color="negative" class="q-ml-sm">
                {{ overdueInspectionsCount }} overdue
              </q-badge>
              <q-badge v-if="dueSoonInspectionsCount > 0" color="warning" class="q-ml-sm">
                {{ dueSoonInspectionsCount }} due soon
              </q-badge>
            </div>
          </q-card-section>

          <!-- Overdue Inspections -->
          <q-card-section v-if="overdueInspections.length > 0">
            <div class="text-subtitle2 text-negative q-mb-sm">Overdue Inspections</div>
            <q-list separator bordered>
              <q-item
                v-for="pue in overdueInspections"
                :key="pue.pue_id"
                clickable
                @click="$router.push({ name: 'pue' })"
              >
                <q-item-section avatar>
                  <q-avatar color="negative" text-color="white" icon="fact_check" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                    {{ pue.name || `PUE #${pue.pue_id}` }}
                    <q-badge color="negative" class="q-ml-sm">
                      Overdue
                    </q-badge>
                  </q-item-label>
                  <q-item-label caption>
                    <template v-if="pue.last_inspection_date">
                      Last inspected: {{ formatDate(pue.last_inspection_date) }}
                    </template>
                    <template v-else>
                      Never inspected
                    </template>
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="arrow_forward"
                    color="primary"
                    @click.stop="$router.push({ name: 'pue' })"
                  />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>

          <!-- Due Soon Inspections -->
          <q-card-section v-if="dueSoonInspections.length > 0">
            <div class="text-subtitle2 text-warning q-mb-sm">Due Soon</div>
            <q-list separator bordered>
              <q-item
                v-for="pue in dueSoonInspections"
                :key="pue.pue_id"
                clickable
                @click="$router.push({ name: 'pue' })"
              >
                <q-item-section avatar>
                  <q-avatar color="warning" text-color="white" icon="fact_check" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>
                    {{ pue.name || `PUE #${pue.pue_id}` }}
                    <q-badge color="warning" class="q-ml-sm">
                      Due Soon
                    </q-badge>
                  </q-item-label>
                  <q-item-label caption>
                    Last inspected: {{ formatDate(pue.last_inspection_date) }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="arrow_forward"
                    color="primary"
                    @click.stop="$router.push({ name: 'pue' })"
                  />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>

          <q-card-section v-if="overdueInspections.length === 0 && dueSoonInspections.length === 0">
            <div class="text-center text-grey-7 q-pa-md">
              <q-icon name="check_circle" size="48px" color="positive" />
              <div class="q-mt-sm">All PUE items are up to date with inspections!</div>
            </div>
          </q-card-section>
        </q-card>
      </div>

    </div>

    <!-- Rental Details Dialog -->
    <q-dialog v-model="showRentalDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Rental Details</div>
        </q-card-section>

        <q-card-section v-if="selectedRental">
          <div class="q-gutter-sm">
            <div><strong>Rental ID:</strong> {{ selectedRental.rentral_id }}</div>
            <div><strong>Battery ID:</strong> {{ selectedRental.battery_id }}</div>
            <div><strong>Hub:</strong> {{ selectedRental.hub_name }}</div>

            <q-separator />

            <div class="text-subtitle2 q-mt-sm">Renter Information</div>
            <div><strong>Name:</strong> {{ selectedRental.user_name }}</div>
            <div><strong>Username:</strong> {{ selectedRental.username }}</div>
            <div><strong>User ID:</strong> {{ selectedRental.user_id }}</div>
            <div v-if="selectedRental.mobile_number">
              <strong>Mobile:</strong>
              <a :href="`tel:${selectedRental.mobile_number}`">{{ selectedRental.mobile_number }}</a>
            </div>
            <div v-if="selectedRental.address"><strong>Address:</strong> {{ selectedRental.address }}</div>

            <q-separator />

            <div class="text-subtitle2 q-mt-sm">Rental Timeline</div>
            <div><strong>Rented On:</strong> {{ formatDate(selectedRental.timestamp_taken) }}</div>
            <div><strong>Due Back:</strong> {{ formatDate(selectedRental.due_back) }}</div>
            <div v-if="selectedRental.status === 'overdue'">
              <strong class="text-negative">Overdue By:</strong>
              {{ selectedRental.days_overdue }} days ({{ Math.floor(selectedRental.hours_overdue) }} hours)
            </div>
            <div v-else>
              <strong class="text-warning">Due In:</strong> {{ selectedRental.days_until_due }} days
            </div>

            <q-separator />

            <div class="text-subtitle2 q-mt-sm">Financial Details</div>
            <div v-if="selectedRental.total_cost">
              <strong>Total Cost:</strong> {{ currencySymbol }}{{ selectedRental.total_cost?.toFixed(2) }}
            </div>
            <div v-if="selectedRental.deposit_amount">
              <strong>Deposit:</strong> {{ currencySymbol }}{{ selectedRental.deposit_amount?.toFixed(2) }}
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn label="Close" flat v-close-popup />
          <q-btn
            label="View Full Rental"
            color="primary"
            :to="{ name: 'rental-detail', params: { id: selectedRental?.rentral_id } }"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { hubsAPI, rentalsAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'
import HubFilter from 'src/components/HubFilter.vue'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useAuthStore } from 'stores/auth'

const $q = useQuasar()
const hubSettingsStore = useHubSettingsStore()
const authStore = useAuthStore()
const selectedHub = ref(null)

const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

const stats = ref({
  batteriesAvailable: 0,
  batteriesMaintenance: 0,
  batteriesRented: 0
})

const batteryList = ref([])
const batterySearchQuery = ref('')
const batteryStatusFilter = ref(null)
const overdueRentals = ref([])
const upcomingRentals = ref([])
const showRentalDialog = ref(false)
const selectedRental = ref(null)

const statusFilterOptions = [
  { label: 'Available', value: 'available' },
  { label: 'Rented', value: 'rented' },
  { label: 'In Maintenance', value: 'maintenance' },
  { label: 'Retired', value: 'retired' }
]

const filteredBatteryList = computed(() => {
  let filtered = batteryList.value

  // Filter by search query
  if (batterySearchQuery.value) {
    const query = batterySearchQuery.value.toLowerCase()
    filtered = filtered.filter(b => {
      const shortId = (b.short_id || '').toLowerCase()
      const batteryId = String(b.battery_id || '')
      return shortId.includes(query) || batteryId.includes(query)
    })
  }

  // Filter by status
  if (batteryStatusFilter.value) {
    filtered = filtered.filter(b => b.status === batteryStatusFilter.value.value)
  }

  return filtered
})

// PUE Inspection alerts
const overdueInspections = ref([])
const dueSoonInspections = ref([])

const overdueCount = computed(() => overdueRentals.value.length)
const upcomingCount = computed(() => upcomingRentals.value.length)
const overdueInspectionsCount = computed(() => overdueInspections.value.length)
const dueSoonInspectionsCount = computed(() => dueSoonInspections.value.length)

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm') + ' UTC'
}

const getBatteryStatusColor = (status) => {
  const colors = {
    'available': 'positive',
    'rented': 'accent',
    'maintenance': 'warning',
    'retired': 'negative'
  }
  return colors[status] || 'grey'
}

const getBatteryStatusIcon = (status) => {
  const icons = {
    'available': 'battery_full',
    'rented': 'electric_bolt',
    'maintenance': 'build',
    'retired': 'block'
  }
  return icons[status] || 'battery_unknown'
}

const formatBatteryStatus = (status) => {
  const labels = {
    'available': 'Available',
    'rented': 'Rented',
    'maintenance': 'In Maintenance',
    'retired': 'Retired'
  }
  return labels[status] || status
}

const showRentalDetails = (rental) => {
  selectedRental.value = rental
  showRentalDialog.value = true
}

const loadDashboardData = async () => {
  $q.loading.show()

  try {
    // Load battery stats by status
    try {
      let allBatteries = []

      if (selectedHub.value) {
        // Load batteries for selected hub only
        const batteriesResponse = await hubsAPI.getBatteries(selectedHub.value)
        const batteries = batteriesResponse.data || []

        // Get hub info
        const hubsResponse = await hubsAPI.list()
        const hub = hubsResponse.data.find(h => h.hub_id === selectedHub.value)
        const hubName = hub ? hub.what_three_word_location : 'Unknown Hub'

        // Add hub name to each battery
        allBatteries = batteries.map(b => ({
          ...b,
          hub_name: hubName
        }))
      } else {
        // Load all hubs to get all batteries
        const hubsResponse = await hubsAPI.list()
        for (const hub of hubsResponse.data) {
          const batteriesResponse = await hubsAPI.getBatteries(hub.hub_id)
          const batteries = batteriesResponse.data || []

          // Add hub name to each battery
          const batteriesWithHub = batteries.map(b => ({
            ...b,
            hub_name: hub.what_three_word_location
          }))

          allBatteries.push(...batteriesWithHub)
        }
      }

      // Store full battery list for display
      batteryList.value = allBatteries

      // Count batteries by status
      stats.value.batteriesAvailable = allBatteries.filter(b => b.status === 'available').length
      stats.value.batteriesMaintenance = allBatteries.filter(b =>
        b.status === 'maintenance' || b.status === 'retired'
      ).length
      stats.value.batteriesRented = allBatteries.filter(b => b.status === 'rented').length
    } catch (error) {
      console.error('Error loading battery stats:', error)
    }

    // Load overdue and upcoming rentals
    try {
      const rentalsResponse = await rentalsAPI.getOverdueUpcoming()
      // Filter by hub if selected (for superadmin only)
      let overdue = rentalsResponse.data.overdue || []
      let upcoming = rentalsResponse.data.upcoming || []

      if (selectedHub.value) {
        overdue = overdue.filter(r => r.hub_id === selectedHub.value)
        upcoming = upcoming.filter(r => r.hub_id === selectedHub.value)
      }

      overdueRentals.value = overdue
      upcomingRentals.value = upcoming
    } catch (error) {
      console.error('Error loading rental alerts:', error)
    }

    // Load PUE inspection alerts
    try {
      let allPUE = []

      if (selectedHub.value) {
        // Load PUE for selected hub only
        const pueResponse = await hubsAPI.getPUE(selectedHub.value)
        allPUE = pueResponse.data || []
      } else {
        // Load all hubs to get all PUE
        const hubsResponse = await hubsAPI.list()
        for (const hub of hubsResponse.data) {
          const pueResponse = await hubsAPI.getPUE(hub.hub_id)
          allPUE.push(...(pueResponse.data || []))
        }
      }

      // Filter by inspection status
      const overdue = allPUE.filter(pue => pue.inspection_status === 'overdue')
      const dueSoon = allPUE.filter(pue => pue.inspection_status === 'due_soon')

      overdueInspections.value = overdue
      dueSoonInspections.value = dueSoon
    } catch (error) {
      console.error('Error loading PUE inspection alerts:', error)
    }

  } catch (error) {
    console.error('Dashboard load error:', error)
    const errorMessage = error.response?.data?.detail ||
                         error.message ||
                         'Failed to load dashboard data'
    $q.notify({
      type: 'negative',
      message: errorMessage,
      position: 'top'
    })
  } finally {
    $q.loading.hide()
  }
}

const onHubChange = (hubId) => {
  selectedHub.value = hubId
  loadDashboardData()
}

onMounted(() => {
  // For non-superadmins, set selectedHub to their hub_id automatically
  if (!authStore.isSuperAdmin && authStore.user?.hub_id) {
    selectedHub.value = authStore.user.hub_id
  }
  loadDashboardData()
})
</script>

<style scoped>
.stat-card {
  height: 100%;
}
</style>
