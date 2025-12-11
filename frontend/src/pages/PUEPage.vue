<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h4">Productive Use Equipment (PUE)</div>
      </div>
      <div class="col-auto row items-center q-gutter-sm">
        <HubFilter v-model="selectedHub" @change="onHubChange" />
        <q-btn
          v-if="authStore.isAdmin"
          label="Add Equipment"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <q-card>
      <q-card-section>
        <q-table
          :rows="pueItems"
          :columns="columns"
          row-key="pue_id"
          :loading="loading"
          :filter="filter"
          :no-data-label="selectedHub ? 'No equipment found for this hub - add some to get started!' : 'No equipment available yet - add your first PUE item!'"
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

          <template v-slot:body-cell-usage_location="props">
            <q-td :props="props">
              <q-badge
                :label="props.row.usage_location"
                outline
              />
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                v-if="authStore.isAdmin"
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click="editPUE(props.row)"
              />
              <q-btn
                v-if="authStore.isSuperAdmin"
                flat
                round
                dense
                icon="delete"
                color="negative"
                @click="deletePUE(props.row)"
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
          <div class="text-h6">{{ editingPUE ? 'Edit Equipment' : 'Add Equipment' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="savePUE" class="q-gutter-md">
            <q-input
              v-if="!editingPUE"
              v-model.number="formData.pue_id"
              label="PUE ID"
              type="number"
              outlined
              :rules="[val => !!val || 'PUE ID is required']"
              hint="Unique identifier for this equipment"
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
              v-model="formData.name"
              label="Equipment Name"
              outlined
              :rules="[val => !!val || 'Name is required']"
            />

            <q-input
              v-model="formData.description"
              label="Description"
              type="textarea"
              outlined
              rows="2"
            />


            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input
                  v-model.number="formData.power_rating_watts"
                  label="Power Rating (W)"
                  type="number"
                  outlined
                />
              </div>
              <div class="col-6">
                <q-input
                  v-model="formData.storage_location"
                  label="Storage Location"
                  outlined
                />
              </div>
            </div>

            <q-select
              v-model="formData.usage_location"
              :options="usageLocationOptions"
              label="Usage Location"
              outlined
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
import { pueAPI, hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'
import HubFilter from 'src/components/HubFilter.vue'

const $q = useQuasar()
const selectedHub = ref(null)
const authStore = useAuthStore()

const pueItems = ref([])
const hubOptions = ref([])
const loading = ref(false)
const filter = ref('')
const showCreateDialog = ref(false)
const editingPUE = ref(null)
const saving = ref(false)

const formData = ref({
  pue_id: null,
  hub_id: null,
  name: '',
  description: '',
  power_rating_watts: null,
  usage_location: 'both',
  storage_location: '',
  status: 'available'
})

const statusOptions = ['available', 'rented', 'maintenance', 'retired']
const usageLocationOptions = ['hub_only', 'battery_only', 'both']

const columns = computed(() => {
  const cols = [
    { name: 'pue_id', label: 'ID', field: 'pue_id', align: 'left', sortable: true }
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
    { name: 'name', label: 'Name', field: 'name', align: 'left', sortable: true },
    { name: 'description', label: 'Description', field: 'description', align: 'left' },
    { name: 'power_rating_watts', label: 'Power (W)', field: 'power_rating_watts', align: 'left' },
    { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
    { name: 'usage_location', label: 'Usage Location', field: 'usage_location', align: 'center' },
    { name: 'actions', label: 'Actions', align: 'center' }
  )

  return cols
})

const getStatusColor = (status) => {
  const colors = {
    available: 'positive',
    rented: 'warning',
    maintenance: 'info',
    retired: 'negative'
  }
  return colors[status] || 'grey'
}

const loadPUE = async () => {
  loading.value = true
  try {
    if (selectedHub.value) {
      // Load PUE for selected hub only
      const pueResponse = await hubsAPI.getPUE(selectedHub.value)
      pueItems.value = pueResponse.data
    } else {
      // Load all hubs to get all PUE
      const hubsResponse = await hubsAPI.list()
      const allPUE = []

      for (const hub of hubsResponse.data) {
        const pueResponse = await hubsAPI.getPUE(hub.hub_id)
        allPUE.push(...pueResponse.data)
      }

      pueItems.value = allPUE
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load equipment',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const onHubChange = (hubId) => {
  selectedHub.value = hubId
  loadPUE()
}

const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

const editPUE = (pue) => {
  editingPUE.value = pue
  formData.value = { ...pue }
  showCreateDialog.value = true
}

const savePUE = async () => {
  saving.value = true
  try {
    if (editingPUE.value) {
      await pueAPI.update(editingPUE.value.pue_id, formData.value)
      $q.notify({
        type: 'positive',
        message: 'Equipment updated successfully',
        position: 'top'
      })
    } else {
      await pueAPI.create(formData.value)
      $q.notify({
        type: 'positive',
        message: 'Equipment created successfully',
        position: 'top'
      })
    }
    showCreateDialog.value = false
    resetForm()
    loadPUE()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to save equipment',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const deletePUE = (pue) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Are you sure you want to delete "${pue.name}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await pueAPI.delete(pue.pue_id)
      $q.notify({
        type: 'positive',
        message: 'Equipment deleted successfully',
        position: 'top'
      })
      loadPUE()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to delete equipment',
        position: 'top'
      })
    }
  })
}

const resetForm = () => {
  formData.value = {
    pue_id: null,
    hub_id: null,
    name: '',
    description: '',
    power_rating_watts: null,
    usage_location: 'both',
    storage_location: '',
    status: 'available'
  }
  editingPUE.value = null
}

onMounted(() => {
  loadPUE()
  loadHubs()
})
</script>
