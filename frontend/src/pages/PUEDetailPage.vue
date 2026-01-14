<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="col-12 col-sm">
        <q-btn flat round dense icon="arrow_back" @click="$router.back()" />
        <span class="text-h5 q-ml-md">{{ pue?.name || `PUE #${pue?.pue_id}` }}</span>
      </div>
      <div class="col-12 col-sm-auto q-gutter-sm">
        <q-btn
          v-if="authStore.isAdmin && pue"
          label="Edit"
          icon="edit"
          color="warning"
          @click="editPUE"
          size="sm"
          class="col-12 col-sm-auto"
        />
      </div>
    </div>

    <div v-if="loading" class="flex flex-center q-pa-xl">
      <q-spinner-gears size="50px" color="primary" />
    </div>

    <div v-else-if="pue" class="row q-col-gutter-md">
      <!-- PUE Information Card -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Equipment Information</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <div><strong>PUE ID:</strong> {{ pue.pue_id }}</div>
            <div v-if="pue.short_id"><strong>Short ID:</strong> {{ pue.short_id }}</div>
            <div><strong>Name:</strong> {{ pue.name }}</div>
            <div v-if="pue.description"><strong>Description:</strong> {{ pue.description }}</div>
            <div v-if="pue.power_rating_watts">
              <strong>Power Rating:</strong> {{ pue.power_rating_watts }}W
            </div>
            <div>
              <strong>Status:</strong>
              <q-badge :color="getStatusColor(pue.status)" class="q-ml-sm">
                {{ pue.status }}
              </q-badge>
            </div>
            <div v-if="pue.usage_location">
              <strong>Usage Location:</strong>
              <q-badge :label="formatUsageLocation(pue.usage_location)" outline />
            </div>
            <div v-if="pue.storage_location">
              <strong>Storage Location:</strong> {{ pue.storage_location }}
            </div>
            <div v-if="pue.rental_count !== undefined">
              <strong>Rental Count:</strong> {{ pue.rental_count }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Inspection Status Card -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Inspection Status</div>
              </div>
              <div class="col-auto">
                <q-btn
                  flat
                  round
                  dense
                  icon="refresh"
                  @click="loadInspections"
                  :loading="loadingInspections"
                />
              </div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div v-if="lastInspection" class="q-gutter-sm">
              <div>
                <strong>Last Inspection:</strong> {{ formatDate(lastInspection.inspection_date) }}
              </div>
              <div>
                <strong>Condition:</strong>
                <q-badge :color="getConditionColor(lastInspection.condition)" class="q-ml-sm">
                  {{ lastInspection.condition }}
                </q-badge>
              </div>
              <div v-if="lastInspection.inspector_id">
                <strong>Inspector ID:</strong> {{ lastInspection.inspector_id }}
              </div>
              <div v-if="lastInspection.issues_found" class="q-mt-sm">
                <strong>Issues:</strong>
                <div class="q-ml-sm text-grey-8">{{ lastInspection.issues_found }}</div>
              </div>
            </div>
            <div v-else class="text-center text-grey-7">
              No inspections recorded yet
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Inspection History -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Inspection History</div>
              </div>
              <div class="col-auto">
                <q-btn
                  label="Record Inspection"
                  icon="add"
                  color="primary"
                  @click="showRecordInspectionDialog = true"
                />
              </div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-table
              :rows="inspections"
              :columns="inspectionColumns"
              row-key="inspection_id"
              :loading="loadingInspections"
              :rows-per-page-options="[10, 20, 50]"
              :pagination="{ rowsPerPage: 10 }"
            >
              <template v-slot:body-cell-condition="props">
                <q-td :props="props">
                  <q-badge :color="getConditionColor(props.row.condition)">
                    {{ props.row.condition }}
                  </q-badge>
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </div>

      <!-- Rental History -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Rental History</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list v-if="rentalHistory.length > 0" separator>
              <q-item
                v-for="rental in rentalHistory"
                :key="rental.pue_rental_id"
                clickable
                :to="{ name: 'pue-rental-detail', params: { id: rental.pue_rental_id } }"
              >
                <q-item-section avatar>
                  <q-icon name="receipt" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Rental #{{ rental.pue_rental_id }}</q-item-label>
                  <q-item-label caption>{{ formatDate(rental.timestamp_taken) }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge :color="rental.date_returned ? 'grey' : 'positive'">
                    {{ rental.date_returned ? 'Returned' : 'Active' }}
                  </q-badge>
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No rental history
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Record Inspection Dialog -->
    <q-dialog v-model="showRecordInspectionDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Record New Inspection</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="recordInspection" class="q-gutter-md">
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
              label="Issues Found"
              type="textarea"
              outlined
              rows="3"
            />

            <q-input
              v-model="inspectionForm.maintenance_notes"
              label="Actions Taken"
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

    <!-- Edit PUE Dialog -->
    <q-dialog v-model="showEditDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Edit Equipment</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="savePUE" class="q-gutter-md">
            <q-input
              v-model="editForm.name"
              label="Equipment Name *"
              outlined
              :rules="[val => !!val || 'Name is required']"
            />

            <q-input
              v-model="editForm.description"
              label="Description"
              type="textarea"
              outlined
              rows="2"
            />

            <div class="row">
              <div class="col q-pr-sm">
                <q-input
                  v-model.number="editForm.power_rating_watts"
                  label="Power Rating (W)"
                  type="number"
                  outlined
                />
              </div>
              <div class="col q-pl-sm">
                <q-input
                  v-model="editForm.storage_location"
                  label="Storage Location"
                  outlined
                />
              </div>
            </div>

            <q-select
              v-model="editForm.usage_location"
              :options="usageLocationOptions"
              label="Usage Location"
              outlined
            />

            <q-select
              v-model="editForm.status"
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
import { pueAPI, pueInspectionsAPI, pueRentalsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar, date } from 'quasar'

const $q = useQuasar()
const route = useRoute()
const authStore = useAuthStore()

const pue = ref(null)
const loading = ref(true)
const inspections = ref([])
const loadingInspections = ref(false)
const rentalHistory = ref([])
const showRecordInspectionDialog = ref(false)
const showEditDialog = ref(false)
const savingInspection = ref(false)
const saving = ref(false)

const inspectionForm = ref({
  inspection_date: new Date().toISOString().slice(0, 16),
  condition: '',
  notes: '',
  maintenance_notes: ''
})

const editForm = ref({
  name: '',
  description: '',
  power_rating_watts: null,
  usage_location: 'both',
  storage_location: '',
  status: 'available'
})

const conditionOptions = ['Excellent', 'Good', 'Fair', 'Poor', 'Damaged']
const usageLocationOptions = ['hub_only', 'battery_only', 'both']
const statusOptions = ['available', 'rented', 'maintenance', 'retired']

const inspectionColumns = [
  { name: 'inspection_date', label: 'Date', field: 'inspection_date', align: 'left', sortable: true, format: val => formatDate(val) },
  { name: 'inspector_id', label: 'Inspector ID', field: 'inspector_id', align: 'left' },
  { name: 'condition', label: 'Condition', field: 'condition', align: 'center' },
  { name: 'issues_found', label: 'Issues', field: 'issues_found', align: 'left' },
  { name: 'actions_taken', label: 'Actions', field: 'actions_taken', align: 'left' }
]

const lastInspection = computed(() => {
  if (inspections.value.length === 0) return null
  return inspections.value[0]
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

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm')
}

const formatUsageLocation = (location) => {
  const map = {
    'hub_only': 'Hub Only',
    'battery_only': 'Battery Only',
    'both': 'Both'
  }
  return map[location] || location
}

const loadPUE = async () => {
  loading.value = true
  try {
    const pueId = route.params.id
    const response = await pueAPI.get(pueId)
    pue.value = response.data

    // Load inspections
    await loadInspections()

    // Load rental history
    await loadRentalHistory()
  } catch (error) {
    console.error('Failed to load PUE:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load equipment details',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const loadInspections = async () => {
  loadingInspections.value = true
  try {
    const pueId = route.params.id
    const response = await pueInspectionsAPI.list(pueId)
    inspections.value = response.data.inspections || []
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

const loadRentalHistory = async () => {
  try {
    const pueId = route.params.id
    // Get all PUE rentals for this PUE
    const response = await pueRentalsAPI.list({ pue_id: pueId })
    rentalHistory.value = response.data || []
  } catch (error) {
    console.error('Failed to load rental history:', error)
  }
}

const recordInspection = async () => {
  savingInspection.value = true
  try {
    const pueId = route.params.id
    const inspectionData = {
      inspector_name: inspectionForm.value.inspector_name,
      inspection_date: inspectionForm.value.inspection_date ? new Date(inspectionForm.value.inspection_date).toISOString() : undefined,
      condition: inspectionForm.value.condition,
      notes: inspectionForm.value.notes || undefined,
      requires_maintenance: inspectionForm.value.requires_maintenance,
      maintenance_notes: inspectionForm.value.requires_maintenance ? inspectionForm.value.maintenance_notes : undefined
    }

    await pueInspectionsAPI.create(pueId, inspectionData)

    $q.notify({
      type: 'positive',
      message: 'Inspection recorded successfully',
      position: 'top'
    })

    showRecordInspectionDialog.value = false
    resetInspectionForm()
    await loadInspections()
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
    inspection_date: new Date().toISOString().slice(0, 16),
    condition: '',
    notes: '',
    maintenance_notes: ''
  }
}

const editPUE = () => {
  editForm.value = {
    name: pue.value.name,
    description: pue.value.description || '',
    power_rating_watts: pue.value.power_rating_watts,
    usage_location: pue.value.usage_location || 'both',
    storage_location: pue.value.storage_location || '',
    status: pue.value.status
  }
  showEditDialog.value = true
}

const savePUE = async () => {
  saving.value = true
  try {
    const pueId = route.params.id
    await pueAPI.update(pueId, editForm.value)

    $q.notify({
      type: 'positive',
      message: 'Equipment updated successfully',
      position: 'top'
    })

    showEditDialog.value = false
    await loadPUE()
  } catch (error) {
    console.error('Failed to update PUE:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to update equipment',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadPUE()
})
</script>
