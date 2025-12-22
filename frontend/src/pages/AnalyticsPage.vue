<template>
  <q-page class="column">
    <div class="q-pa-md">
      <div class="text-h4 q-mb-md">Analytics Dashboard</div>

      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-12 col-md-4">
          <q-select
            v-model="selectedHub"
            :options="hubOptions"
            option-value="hub_id"
            option-label="what_three_word_location"
            emit-value
            map-options
            label="Select Hub"
            outlined
            dense
          />
        </div>

        <div class="col-12 col-md-4">
          <q-select
            v-model="timePeriod"
            :options="timePeriodOptions"
            label="Time Period"
            outlined
            dense
          />
        </div>

        <div class="col-12 col-md-4">
          <q-btn
            label="Refresh"
            icon="refresh"
            color="primary"
            @click="refreshDashboard"
            :loading="loading"
          />
        </div>
      </div>
    </div>

    <!-- Panel Dashboard iframe -->
    <div class="col q-pa-md">
      <q-card class="full-height">
        <q-card-section class="full-height">
          <iframe
            v-if="panelUrl"
            :src="panelUrl"
            class="panel-iframe"
            frameborder="0"
            @load="onPanelLoad"
          />
          <div v-else class="flex flex-center full-height">
            <div class="text-center">
              <q-icon name="analytics" size="64px" color="grey-5" />
              <div class="text-h6 text-grey-7 q-mt-md">
                Interactive Analytics Dashboard
              </div>
              <div class="text-grey-6 q-mt-sm">
                Powered by Panel HoloViews
              </div>
              <q-btn
                label="Load Dashboard"
                color="primary"
                class="q-mt-md"
                @click="loadPanelDashboard"
              />
            </div>
          </div>

          <q-inner-loading :showing="loading">
            <q-spinner-gears size="50px" color="primary" />
          </q-inner-loading>
        </q-card-section>
      </q-card>
    </div>

    <!-- Quick Analytics Cards (Static - for when Panel is not available) -->
    <div v-if="!panelUrl" class="q-pa-md">
      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
          <q-card>
            <q-card-section>
              <div class="text-h6">Revenue Overview</div>
            </q-card-section>
            <q-card-section>
              <div class="text-h4 text-primary">
                {{ currencySymbol }}{{ revenueData.total_revenue?.toFixed(2) || '0.00' }}
              </div>
              <div class="text-grey-7">Total Revenue ({{ timePeriod }})</div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-md-6">
          <q-card>
            <q-card-section>
              <div class="text-h6">Battery Performance</div>
            </q-card-section>
            <q-card-section>
              <div class="text-grey-7">
                Select a hub to view detailed analytics
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { hubsAPI, analyticsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const authStore = useAuthStore()
const hubSettingsStore = useHubSettingsStore()

const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

const hubOptions = ref([])
const selectedHub = ref(null)
const timePeriod = ref('last_month')
const loading = ref(false)
const panelLoaded = ref(false)
const revenueData = ref({})

const timePeriodOptions = [
  'last_24_hours',
  'last_week',
  'last_2_weeks',
  'last_month',
  'last_2_months',
  'last_3_months',
  'last_6_months',
  'last_year',
  'this_week',
  'this_month',
  'this_year'
]

const panelUrl = computed(() => {
  const panelBaseUrl = process.env.PANEL_URL || 'http://localhost:5100'

  if (!panelLoaded.value) {
    return null
  }

  // Check if user is authenticated
  if (!authStore.token) {
    $q.notify({
      type: 'negative',
      message: 'Please log in to access the analytics dashboard',
      position: 'top'
    })
    return null
  }

  // Build Panel URL with JWT token for authentication
  const params = new URLSearchParams()

  // Pass the JWT token for authentication
  params.append('token', authStore.token)

  if (selectedHub.value) {
    params.append('hub_id', selectedHub.value)
  }

  params.append('time_period', timePeriod.value)

  return `${panelBaseUrl}/battery_analytics_v3?${params.toString()}`
})

const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data

    if (hubOptions.value.length > 0) {
      selectedHub.value = hubOptions.value[0].hub_id
    }
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

const loadRevenueData = async () => {
  try {
    const response = await analyticsAPI.revenue({
      time_period: timePeriod.value
    })
    revenueData.value = response.data
  } catch (error) {
    console.error('Failed to load revenue data:', error)
  }
}

const loadPanelDashboard = () => {
  panelLoaded.value = true
  loading.value = true
}

const onPanelLoad = () => {
  loading.value = false
}

const refreshDashboard = () => {
  if (panelLoaded.value) {
    // Reload iframe
    const iframe = document.querySelector('.panel-iframe')
    if (iframe) {
      iframe.src = iframe.src
    }
  }
  loadRevenueData()
}

onMounted(() => {
  loadHubs()
  loadRevenueData()
})
</script>

<style scoped>
.panel-iframe {
  width: 100%;
  height: 100%;
  min-height: 1200px;
}

.full-height {
  height: 100%;
  min-height: 1200px;
}
</style>
