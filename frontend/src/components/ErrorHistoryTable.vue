<template>
  <q-card flat bordered>
    <q-card-section>
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6">Error History</div>
        <q-select
          v-model="timePeriod"
          :options="timeOptions"
          dense
          outlined
          style="min-width: 150px"
          @update:model-value="loadErrors"
        />
      </div>

      <div v-if="!loading && errors.length === 0" class="text-center q-pa-lg text-grey-6">
        <q-icon name="check_circle" size="48px" class="q-mb-sm" />
        <div class="text-body1">No errors recorded in this time period</div>
        <div class="text-caption">Battery is operating normally</div>
      </div>

      <q-table
        v-else
        :rows="errors"
        :columns="columns"
        row-key="id"
        :loading="loading"
        flat
        :pagination="pagination"
        class="error-history-table"
      >
        <template v-slot:body-cell-timestamp="props">
          <q-td :props="props">
            <div class="text-body2">{{ formatDate(props.row.timestamp) }}</div>
            <div class="text-caption text-grey-6">{{ formatTime(props.row.timestamp) }}</div>
          </q-td>
        </template>

        <template v-slot:body-cell-errors="props">
          <q-td :props="props">
            <div class="column q-gutter-xs">
              <q-badge
                v-for="error in props.row.decoded_errors"
                :key="error.code"
                :color="getSeverityColor(error.severity)"
                :label="error.description"
                class="q-pa-xs"
              >
                <q-tooltip>
                  <div><strong>Code:</strong> {{ error.code }}</div>
                  <div><strong>Type:</strong> {{ error.name }}</div>
                  <div><strong>Severity:</strong> {{ error.severity }}</div>
                </q-tooltip>
              </q-badge>
            </div>
          </q-td>
        </template>

        <template v-slot:body-cell-metrics="props">
          <q-td :props="props">
            <div class="text-caption">
              <div v-if="props.row.other_metrics.soc !== null">
                <strong>SOC:</strong> {{ props.row.other_metrics.soc?.toFixed(1) }}%
              </div>
              <div v-if="props.row.other_metrics.voltage !== null">
                <strong>Voltage:</strong> {{ props.row.other_metrics.voltage?.toFixed(2) }}V
              </div>
              <div v-if="props.row.other_metrics.temperature !== null">
                <strong>Temp:</strong> {{ props.row.other_metrics.temperature?.toFixed(1) }}°C
              </div>
            </div>
          </q-td>
        </template>
      </q-table>

      <div v-if="errors.length > 0" class="q-mt-md text-caption text-grey-6">
        {{ errors.length }} error{{ errors.length !== 1 ? 's' : '' }} found in {{ timeOptions.find(o => o.value === timePeriod)?.label || timePeriod }}
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { batteriesAPI } from '../services/api'
import { date } from 'quasar'

const props = defineProps({
  batteryId: {
    type: Number,
    required: true
  }
})

const errors = ref([])
const loading = ref(false)
const timePeriod = ref('last_week')

const timeOptions = [
  { label: 'Last 24 Hours', value: 'last_24_hours' },
  { label: 'Last Week', value: 'last_week' },
  { label: 'Last Month', value: 'last_month' },
  { label: 'Last Year', value: 'last_year' }
]

const pagination = ref({
  rowsPerPage: 10
})

const columns = [
  {
    name: 'timestamp',
    label: 'Time',
    field: 'timestamp',
    sortable: true,
    align: 'left'
  },
  {
    name: 'errors',
    label: 'Errors',
    field: 'decoded_errors',
    sortable: false,
    align: 'left',
    style: 'min-width: 200px'
  },
  {
    name: 'metrics',
    label: 'Metrics at Error',
    field: 'other_metrics',
    sortable: false,
    align: 'left'
  }
]

function getSeverityColor(severity) {
  switch (severity) {
    case 'error':
      return 'negative'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    default:
      return 'grey'
  }
}

function formatDate(timestamp) {
  if (!timestamp) return '-'
  return date.formatDate(timestamp, 'MMM D, YYYY')
}

function formatTime(timestamp) {
  if (!timestamp) return '-'
  return date.formatDate(timestamp, 'h:mm A')
}

async function loadErrors() {
  loading.value = true
  try {
    const response = await batteriesAPI.getErrors(props.batteryId, timePeriod.value)
    errors.value = response.data.errors
  } catch (error) {
    console.error('Failed to load battery errors:', error)
    errors.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadErrors()
})
</script>

<style scoped>
.error-history-table {
  /* Ensure table is responsive */
}
</style>
