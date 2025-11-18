<template>
  <q-page class="q-pa-md">
    <div class="text-h4 q-mb-md">Webhook Logs</div>

    <q-card>
      <q-card-section>
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-12 col-md-4">
            <q-input
              v-model="filters.battery_id"
              label="Battery ID"
              outlined
              dense
              clearable
            />
          </div>
          <div class="col-12 col-md-4">
            <q-select
              v-model="filters.status"
              :options="statusOptions"
              label="Status"
              outlined
              dense
              clearable
            />
          </div>
          <div class="col-12 col-md-4">
            <q-btn
              label="Apply Filters"
              icon="filter_list"
              color="primary"
              @click="loadLogs"
            />
          </div>
        </div>

        <q-table
          :rows="logs"
          :columns="columns"
          row-key="id"
          :loading="loading"
          :pagination="pagination"
        >
          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-badge
                :color="props.row.status === 'success' ? 'positive' : 'negative'"
                :label="props.row.status"
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

        <q-card-section v-if="selectedLog">
          <div class="q-gutter-sm">
            <div><strong>ID:</strong> {{ selectedLog.id }}</div>
            <div><strong>Battery ID:</strong> {{ selectedLog.battery_id }}</div>
            <div><strong>Status:</strong> {{ selectedLog.status }}</div>
            <div><strong>Timestamp:</strong> {{ formatDate(selectedLog.timestamp) }}</div>

            <div v-if="selectedLog.payload" class="q-mt-md">
              <div class="text-subtitle2">Payload:</div>
              <pre class="code-block">{{ JSON.stringify(selectedLog.payload, null, 2) }}</pre>
            </div>

            <div v-if="selectedLog.error_message" class="q-mt-md">
              <div class="text-subtitle2 text-negative">Error Message:</div>
              <div class="text-negative">{{ selectedLog.error_message }}</div>
            </div>
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
import { ref, onMounted } from 'vue'
import { adminAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'

const $q = useQuasar()

const logs = ref([])
const loading = ref(false)
const showDetailsDialog = ref(false)
const selectedLog = ref(null)

const filters = ref({
  battery_id: null,
  status: null
})

const pagination = ref({
  rowsPerPage: 20
})

const statusOptions = ['success', 'error']

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true },
  { name: 'battery_id', label: 'Battery ID', field: 'battery_id', align: 'left', sortable: true },
  { name: 'timestamp', label: 'Timestamp', field: 'timestamp', align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm:ss')
}

const loadLogs = async () => {
  loading.value = true

  try {
    const params = {}

    if (filters.value.battery_id) {
      params.battery_id = filters.value.battery_id
    }

    if (filters.value.status) {
      params.status = filters.value.status
    }

    const response = await adminAPI.getWebhookLogs(params)
    logs.value = response.data
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load webhook logs',
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

onMounted(() => {
  loadLogs()
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
