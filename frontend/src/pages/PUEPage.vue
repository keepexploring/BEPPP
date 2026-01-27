<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="col-12 col-sm-auto">
        <div class="text-h5">Productive Use Equipment (PUE)</div>
      </div>
      <div class="col-12 col-sm row items-center q-gutter-sm">
        <HubFilter v-model="selectedHub" @change="onHubChange" />
        <q-btn
          v-if="authStore.isAdmin"
          label="Add Equipment"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
          size="sm"
          class="col-12 col-sm-auto"
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
          @row-click="(evt, row) => $router.push({ name: 'pue-detail', params: { id: row.pue_id } })"
          class="cursor-pointer"
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

          <template v-slot:body-cell-inspection_status="props">
            <q-td :props="props">
              <q-badge
                v-if="props.row.inspection_status"
                :color="getInspectionStatusColor(props.row.inspection_status)"
                :label="getInspectionStatusLabel(props.row.inspection_status)"
              >
                <q-tooltip v-if="props.row.last_inspection_date">
                  Last inspection: {{ formatDate(props.row.last_inspection_date) }}
                </q-tooltip>
              </q-badge>
              <q-badge v-else color="grey" label="No data" />
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                dense
                icon="fact_check"
                color="info"
                @click="openInspectionDialog(props.row)"
              >
                <q-tooltip>Inspections</q-tooltip>
              </q-btn>
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
              v-model="formData.pue_id"
              label="PUE ID"
              type="text"
              outlined
              :rules="[val => !!val || 'PUE ID is required']"
              hint="Unique identifier (e.g., PUE-001, P-123-ABC)"
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
              :disable="!!editingPUE"
              @update:model-value="onHubSelected"
            />

            <q-select
              v-model="formData.pue_type_id"
              :options="pueTypeOptions"
              option-value="type_id"
              option-label="type_name"
              emit-value
              map-options
              label="Equipment Type"
              outlined
              clearable
              :disable="!formData.hub_id && !editingPUE"
              :hint="formData.hub_id || editingPUE ? 'Optional - categorize this equipment' : 'Select a hub first'"
            >
              <template v-slot:prepend>
                <q-icon name="category" />
              </template>
            </q-select>

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

            <div class="row">
              <div class="col q-pr-sm">
                <q-input
                  v-model.number="formData.power_rating_watts"
                  label="Power Rating (W)"
                  type="number"
                  outlined
                />
              </div>
              <div class="col q-pl-sm">
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

    <!-- Inspection Dialog -->
    <q-dialog v-model="showInspectionDialog">
      <q-card style="min-width: 700px">
        <q-card-section>
          <div class="text-h6">Inspections - {{ selectedPUE?.name || `PUE #${selectedPUE?.pue_id}` }}</div>
        </q-card-section>

        <q-separator />

        <q-card-section>
          <div class="row items-center q-mb-md">
            <div class="col">
              <div class="text-subtitle1">Inspection History</div>
            </div>
            <div class="col-auto">
              <q-btn
                label="Record New Inspection"
                icon="add"
                color="primary"
                @click="showRecordInspectionDialog = true"
              />
            </div>
          </div>

          <q-table
            :rows="inspections"
            :columns="inspectionColumns"
            row-key="inspection_id"
            :loading="loadingInspections"
            :rows-per-page-options="[5, 10, 20]"
          >
            <template v-slot:body-cell-condition="props">
              <q-td :props="props">
                <q-badge :color="getConditionColor(props.row.condition)">
                  {{ props.row.condition }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-requires_maintenance="props">
              <q-td :props="props">
                <q-icon
                  :name="props.row.requires_maintenance ? 'warning' : 'check_circle'"
                  :color="props.row.requires_maintenance ? 'warning' : 'positive'"
                  size="sm"
                />
              </q-td>
            </template>
          </q-table>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn label="Close" flat v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Record Inspection Dialog -->
    <q-dialog v-model="showRecordInspectionDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Record New Inspection</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="recordInspection" class="q-gutter-md">
            <q-input
              v-model="inspectionForm.inspector_name"
              label="Inspector Name *"
              outlined
              :rules="[val => !!val || 'Inspector name is required']"
            />

            <q-input
              v-model="inspectionForm.inspection_date"
              label="Inspection Date"
              type="datetime-local"
              outlined
            />

            <q-select
              v-model="inspectionForm.condition"
              :options="conditionOptions"
              label="Condition *"
              outlined
              :rules="[val => !!val || 'Condition is required']"
            />

            <q-input
              v-model="inspectionForm.notes"
              label="Inspection Notes"
              type="textarea"
              outlined
              rows="3"
            />

            <q-checkbox
              v-model="inspectionForm.requires_maintenance"
              label="Requires Maintenance"
            />

            <q-input
              v-if="inspectionForm.requires_maintenance"
              v-model="inspectionForm.maintenance_notes"
              label="Maintenance Notes"
              type="textarea"
              outlined
              rows="2"
            />

            <div class="row justify-end q-gutter-sm">
              <q-btn label="Cancel" flat v-close-popup />
              <q-btn
                label="Record Inspection"
                type="submit"
                color="primary"
                :loading="savingInspection"
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
import { pueAPI, hubsAPI, pueInspectionsAPI, settingsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'
import HubFilter from 'src/components/HubFilter.vue'

const $q = useQuasar()
const selectedHub = ref(null)
const authStore = useAuthStore()

const pueItems = ref([])
const hubOptions = ref([])
const pueTypeOptions = ref([])
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
  pue_type_id: null,
  power_rating_watts: null,
  usage_location: 'both',
  storage_location: '',
  status: 'available'
})

// Inspection state
const showInspectionDialog = ref(false)
const showRecordInspectionDialog = ref(false)
const selectedPUE = ref(null)
const inspections = ref([])
const loadingInspections = ref(false)
const savingInspection = ref(false)

const inspectionForm = ref({
  inspector_name: '',
  inspection_date: new Date().toISOString().slice(0, 16),
  condition: '',
  notes: '',
  requires_maintenance: false,
  maintenance_notes: ''
})

const statusOptions = ['available', 'rented', 'maintenance', 'retired']
const usageLocationOptions = ['hub_only', 'battery_only', 'both']
const conditionOptions = ['Excellent', 'Good', 'Fair', 'Poor', 'Damaged']

const inspectionColumns = [
  { name: 'inspection_date', label: 'Date', field: 'inspection_date', align: 'left', sortable: true, format: val => formatDate(val) },
  { name: 'inspector_name', label: 'Inspector', field: 'inspector_name', align: 'left' },
  { name: 'condition', label: 'Condition', field: 'condition', align: 'center' },
  { name: 'requires_maintenance', label: 'Maintenance', field: 'requires_maintenance', align: 'center' },
  { name: 'notes', label: 'Notes', field: 'notes', align: 'left' }
]

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
    { name: 'inspection_status', label: 'Inspection', field: 'inspection_status', align: 'center', sortable: true },
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

const getInspectionStatusColor = (status) => {
  const colors = {
    ok: 'positive',
    due_soon: 'warning',
    overdue: 'negative',
    never_inspected: 'grey'
  }
  return colors[status] || 'grey'
}

const getInspectionStatusLabel = (status) => {
  const labels = {
    ok: 'OK',
    due_soon: 'Due Soon',
    overdue: 'Overdue',
    never_inspected: 'Not Inspected'
  }
  return labels[status] || status
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

const getConditionColor = (condition) => {
  const colors = {
    'Excellent': 'positive',
    'Good': 'positive',
    'Fair': 'warning',
    'Poor': 'negative',
    'Damaged': 'negative'
  }
  return colors[condition] || 'grey'
}

const openInspectionDialog = async (pue) => {
  selectedPUE.value = pue
  showInspectionDialog.value = true
  await loadInspections(pue.pue_id)
}

const loadInspections = async (pueId) => {
  loadingInspections.value = true
  try {
    const response = await pueInspectionsAPI.list(pueId)
    inspections.value = response.data || []
  } catch (error) {
    console.error('Failed to load inspections:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load inspections',
      position: 'top'
    })
  } finally {
    loadingInspections.value = false
  }
}

const recordInspection = async () => {
  if (!selectedPUE.value) return

  savingInspection.value = true
  try {
    const inspectionData = {
      inspector_name: inspectionForm.value.inspector_name,
      inspection_date: inspectionForm.value.inspection_date ? new Date(inspectionForm.value.inspection_date).toISOString() : undefined,
      condition: inspectionForm.value.condition,
      notes: inspectionForm.value.notes || undefined,
      requires_maintenance: inspectionForm.value.requires_maintenance,
      maintenance_notes: inspectionForm.value.requires_maintenance ? inspectionForm.value.maintenance_notes : undefined
    }

    await pueInspectionsAPI.create(selectedPUE.value.pue_id, inspectionData)

    $q.notify({
      type: 'positive',
      message: 'Inspection recorded successfully',
      position: 'top'
    })

    showRecordInspectionDialog.value = false
    resetInspectionForm()
    await loadInspections(selectedPUE.value.pue_id)
    await loadPUE() // Refresh main list to update inspection status
  } catch (error) {
    console.error('Failed to record inspection:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to record inspection',
      position: 'top'
    })
  } finally {
    savingInspection.value = false
  }
}

const resetInspectionForm = () => {
  inspectionForm.value = {
    inspector_name: '',
    inspection_date: new Date().toISOString().slice(0, 16),
    condition: '',
    notes: '',
    requires_maintenance: false,
    maintenance_notes: ''
  }
}

const loadPUE = async () => {
  loading.value = true
  try {
    console.log('[PUEPage] Loading PUE for hub:', selectedHub.value)
    if (selectedHub.value) {
      // Load PUE for selected hub only
      const pueResponse = await hubsAPI.getPUE(selectedHub.value)
      console.log('[PUEPage] PUE response for hub:', pueResponse.data)
      pueItems.value = pueResponse.data
    } else {
      // Load all hubs to get all PUE
      const hubsResponse = await hubsAPI.list()
      console.log('[PUEPage] Loaded hubs:', hubsResponse.data)
      const allPUE = []

      for (const hub of hubsResponse.data) {
        console.log('[PUEPage] Loading PUE for hub:', hub.hub_id)
        const pueResponse = await hubsAPI.getPUE(hub.hub_id)
        console.log('[PUEPage] PUE response:', pueResponse.data)
        allPUE.push(...pueResponse.data)
      }

      console.log('[PUEPage] Total PUE items loaded:', allPUE.length)
      pueItems.value = allPUE
    }
  } catch (error) {
    console.error('[PUEPage] Failed to load PUE:', error)
    console.error('[PUEPage] Error details:', error.response?.data)
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

const loadPUETypes = async (hubId = null) => {
  try {
    console.log('[PUEPage] Loading PUE types for hubId:', hubId)
    const response = await settingsAPI.getPUETypes(hubId)
    console.log('[PUEPage] PUE types response:', response.data)
    pueTypeOptions.value = response.data?.pue_types || []
    console.log('[PUEPage] Loaded PUE type options:', pueTypeOptions.value)
  } catch (error) {
    console.error('[PUEPage] Failed to load PUE types:', error)
    console.error('[PUEPage] Error details:', error.response?.data)
  }
}

const onHubSelected = (hubId) => {
  // Clear the PUE type selection when hub changes
  formData.value.pue_type_id = null
  // Load PUE types for the selected hub
  if (hubId) {
    loadPUETypes(hubId)
  } else {
    pueTypeOptions.value = []
  }
}

const editPUE = async (pue) => {
  console.log('[PUEPage] Editing PUE:', pue)
  editingPUE.value = pue
  formData.value = { ...pue }
  console.log('[PUEPage] Form data set:', formData.value)
  // Load PUE types for the hub when editing
  if (pue.hub_id) {
    console.log('[PUEPage] Loading PUE types for edit, hub_id:', pue.hub_id)
    await loadPUETypes(pue.hub_id)
    console.log('[PUEPage] PUE types loaded, count:', pueTypeOptions.value.length)
  }
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
      const result = await pueAPI.create(formData.value)
      $q.notify({
        type: 'positive',
        message: result.short_id
          ? `Equipment created successfully! ID: ${result.short_id}`
          : 'Equipment created successfully',
        position: 'top',
        timeout: 5000
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
    pue_type_id: null,
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
  // PUE types will be loaded when a hub is selected
})
</script>
