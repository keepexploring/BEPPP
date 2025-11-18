<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <q-btn flat round dense icon="arrow_back" @click="$router.back()" />
        <span class="text-h4 q-ml-md">{{ battery?.serial_number || 'Battery Details' }}</span>
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
            <div><strong>ID:</strong> {{ battery.id }}</div>
            <div><strong>Serial Number:</strong> {{ battery.serial_number }}</div>
            <div><strong>Capacity:</strong> {{ battery.capacity }}Wh</div>
            <div><strong>Model:</strong> {{ battery.model || 'N/A' }}</div>
            <div>
              <strong>Status:</strong>
              <q-badge :color="getStatusColor(battery.status)" class="q-ml-sm">
                {{ battery.status }}
              </q-badge>
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
              <div v-if="latestData.timestamp">
                <strong>Last Update:</strong> {{ formatDate(latestData.timestamp) }}
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
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { batteriesAPI, dataAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'

const $q = useQuasar()
const route = useRoute()

const battery = ref(null)
const latestData = ref(null)
const loading = ref(true)
const loadingData = ref(false)

const getStatusColor = (status) => {
  const colors = {
    available: 'positive',
    rented: 'warning',
    maintenance: 'info',
    retired: 'negative'
  }
  return colors[status] || 'grey'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm:ss')
}

const loadBatteryDetails = async () => {
  loading.value = true

  try {
    const batteryId = route.params.id

    const response = await batteriesAPI.get(batteryId)
    battery.value = response.data

    await loadLatestData()
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

onMounted(() => {
  loadBatteryDetails()
})
</script>
