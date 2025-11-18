<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h4">Batteries</div>
      </div>
      <div class="col-auto">
        <q-btn
          v-if="authStore.isAdmin"
          label="Add Battery"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <q-card>
      <q-card-section>
        <q-table
          :rows="batteries"
          :columns="columns"
          row-key="id"
          :loading="loading"
          :filter="filter"
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
                :to="{ name: 'battery-detail', params: { id: props.row.id } }"
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
            <q-select
              v-model="formData.hub_id"
              :options="hubOptions"
              option-value="id"
              option-label="name"
              emit-value
              map-options
              label="Hub"
              outlined
              :rules="[val => !!val || 'Hub is required']"
            />

            <q-input
              v-model="formData.serial_number"
              label="Serial Number"
              outlined
              :rules="[val => !!val || 'Serial number is required']"
            />

            <q-input
              v-model.number="formData.capacity"
              label="Capacity (Wh)"
              type="number"
              outlined
              :rules="[val => !!val || 'Capacity is required']"
            />

            <q-select
              v-model="formData.status"
              :options="statusOptions"
              label="Status"
              outlined
            />

            <q-input
              v-model="formData.model"
              label="Model"
              outlined
            />

            <div v-if="authStore.isSuperAdmin && !editingBattery" class="q-gutter-sm">
              <q-input
                v-model="batterySecret"
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
import { ref, onMounted } from 'vue'
import { batteriesAPI, hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const authStore = useAuthStore()

const batteries = ref([])
const hubOptions = ref([])
const loading = ref(false)
const filter = ref('')
const showCreateDialog = ref(false)
const editingBattery = ref(null)
const saving = ref(false)
const batterySecret = ref('')

const formData = ref({
  hub_id: null,
  serial_number: '',
  capacity: null,
  status: 'available',
  model: ''
})

const statusOptions = ['available', 'rented', 'maintenance', 'retired']

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true },
  { name: 'serial_number', label: 'Serial Number', field: 'serial_number', align: 'left', sortable: true },
  { name: 'capacity', label: 'Capacity (Wh)', field: 'capacity', align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
  { name: 'model', label: 'Model', field: 'model', align: 'left' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

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
    // Load all hubs to get all batteries
    const hubsResponse = await hubsAPI.list()
    const allBatteries = []

    for (const hub of hubsResponse.data) {
      const batteriesResponse = await hubsAPI.getBatteries(hub.id)
      allBatteries.push(...batteriesResponse.data)
    }

    batteries.value = allBatteries
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load batteries',
      position: 'top'
    })
  } finally {
    loading.value = false
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

const editBattery = (battery) => {
  editingBattery.value = battery
  formData.value = { ...battery }
  showCreateDialog.value = true
}

const saveBattery = async () => {
  saving.value = true
  try {
    if (editingBattery.value) {
      await batteriesAPI.update(editingBattery.value.id, formData.value)
      $q.notify({
        type: 'positive',
        message: 'Battery updated successfully',
        position: 'top'
      })
    } else {
      const response = await batteriesAPI.create(formData.value)

      // Set battery secret if provided
      if (batterySecret.value && authStore.isSuperAdmin) {
        await batteriesAPI.setBatterySecret(response.data.id, batterySecret.value)
      }

      $q.notify({
        type: 'positive',
        message: 'Battery created successfully',
        position: 'top'
      })
    }
    showCreateDialog.value = false
    resetForm()
    loadBatteries()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to save battery',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const deleteBattery = (battery) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Are you sure you want to delete battery "${battery.serial_number}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await batteriesAPI.delete(battery.id)
      $q.notify({
        type: 'positive',
        message: 'Battery deleted successfully',
        position: 'top'
      })
      loadBatteries()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to delete battery',
        position: 'top'
      })
    }
  })
}

const resetForm = () => {
  formData.value = {
    hub_id: null,
    serial_number: '',
    capacity: null,
    status: 'available',
    model: ''
  }
  batterySecret.value = ''
  editingBattery.value = null
}

onMounted(() => {
  loadBatteries()
  loadHubs()
})
</script>
