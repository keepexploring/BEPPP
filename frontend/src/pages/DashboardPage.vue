<template>
  <q-page class="q-pa-md">
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h4">Dashboard</div>
      <HubFilter v-model="selectedHub" @change="onHubChange" />
    </div>

    <div class="row q-col-gutter-md">
      <!-- Summary Cards -->
      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Total Hubs</div>
                <div class="text-h4">{{ stats.totalHubs }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="hub" size="48px" color="primary" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Active Batteries</div>
                <div class="text-h4">{{ stats.activeBatteries }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="battery_charging_full" size="48px" color="positive" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Active Rentals</div>
                <div class="text-h4">{{ stats.activeRentals }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="receipt" size="48px" color="accent" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Total Revenue</div>
                <div class="text-h4">{{ currencySymbol }}{{ stats.totalRevenue }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="attach_money" size="48px" color="warning" />
              </div>
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

      <!-- Hub Summary -->
      <div class="col-12 col-md-8">
        <q-card>
          <q-card-section>
            <div class="text-h6">Hub Summary</div>
          </q-card-section>
          <q-card-section>
            <q-list v-if="hubSummary.length > 0" separator>
              <q-item v-for="hub in hubSummary" :key="hub.hub_id">
                <q-item-section>
                  <q-item-label>{{ hub.hub_name }}</q-item-label>
                  <q-item-label caption>
                    {{ hub.total_batteries }} batteries, {{ hub.active_batteries }} active
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="arrow_forward"
                    :to="{ name: 'hub-detail', params: { id: hub.hub_id } }"
                  />
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No hubs available
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Recent Activity -->
      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">Quick Actions</div>
          </q-card-section>
          <q-card-section class="q-gutter-sm">
            <q-btn
              label="New Rental"
              icon="add"
              color="primary"
              class="full-width"
              :to="{ name: 'rentals' }"
            />
            <q-btn
              label="Returns"
              icon="assignment_return"
              color="positive"
              outline
              class="full-width"
              :to="{ name: 'rentals', query: { action: 'returns' } }"
            />
            <q-btn
              label="Add Battery"
              icon="battery_plus"
              color="secondary"
              outline
              class="full-width"
              :to="{ name: 'batteries' }"
            />
            <q-btn
              label="View Analytics"
              icon="analytics"
              color="accent"
              outline
              class="full-width"
              :to="{ name: 'analytics' }"
            />
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
import { hubsAPI, analyticsAPI, rentalsAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'
import HubFilter from 'src/components/HubFilter.vue'
import { useHubSettingsStore } from 'stores/hubSettings'

const $q = useQuasar()
const hubSettingsStore = useHubSettingsStore()
const selectedHub = ref(null)

const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

const stats = ref({
  totalHubs: 0,
  activeBatteries: 0,
  activeRentals: 0,
  totalRevenue: 0
})

const hubSummary = ref([])
const overdueRentals = ref([])
const upcomingRentals = ref([])
const showRentalDialog = ref(false)
const selectedRental = ref(null)

const overdueCount = computed(() => overdueRentals.value.length)
const upcomingCount = computed(() => upcomingRentals.value.length)

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm')
}

const showRentalDetails = (rental) => {
  selectedRental.value = rental
  showRentalDialog.value = true
}

const loadDashboardData = async () => {
  $q.loading.show()

  try {
    // Load hub summary with optional hub filter
    const hubParams = selectedHub.value ? { hub_id: selectedHub.value } : {}
    const hubsResponse = await analyticsAPI.hubSummary(hubParams)
    hubSummary.value = hubsResponse.data

    // Filter hub summary by selected hub if needed
    const filteredHubSummary = selectedHub.value
      ? hubSummary.value.filter(h => h.hub_id === selectedHub.value)
      : hubSummary.value

    // Calculate stats
    stats.value.totalHubs = filteredHubSummary.length
    stats.value.activeBatteries = filteredHubSummary.reduce(
      (sum, hub) => sum + (hub.active_batteries || 0),
      0
    )

    // Load active rentals count (active + overdue, excludes returned)
    try {
      const rentalParams = { status: 'active' }
      if (selectedHub.value) {
        rentalParams.hub_id = selectedHub.value
      }
      const activeRentalsResponse = await rentalsAPI.list(rentalParams)
      // Count all batteries that are out (not returned) - includes both active and overdue
      const batteriesOut = activeRentalsResponse.data.filter(r => r.status !== 'returned')
      stats.value.activeRentals = batteriesOut.length
    } catch (error) {
      console.error('Error loading active rentals:', error)
    }

    // Load overdue and upcoming rentals
    try {
      const rentalsResponse = await rentalsAPI.getOverdueUpcoming()
      // Filter by hub if selected
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

    // Load revenue data
    try {
      const revenueParams = { time_period: 'last_month' }
      if (selectedHub.value) {
        revenueParams.hub_id = selectedHub.value
      }
      const revenueResponse = await analyticsAPI.revenue(revenueParams)
      if (revenueResponse.data?.total_revenue) {
        stats.value.totalRevenue = revenueResponse.data.total_revenue.toFixed(2)
      }
    } catch (error) {
      console.error('Error loading revenue:', error)
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
  loadDashboardData()
})
</script>

<style scoped>
.stat-card {
  height: 100%;
}
</style>
