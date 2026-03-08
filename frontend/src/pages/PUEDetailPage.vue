<template>
  <q-page class="q-pa-md">
    <q-banner v-if="isOffline" class="bg-orange text-white q-mb-md" rounded>
      <template v-slot:avatar>
        <q-icon name="cloud_off" />
      </template>
      You are offline. Showing cached data.
    </q-banner>

    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="col-12 col-sm">
        <q-btn flat round dense icon="arrow_back" @click="$router.back()" />
        <span class="text-h5 q-ml-md">{{ pue?.name || `PUE #${pue?.pue_id}` }}</span>
      </div>
      <div class="col-12 col-sm-auto q-gutter-sm">
        <q-btn
          v-if="pue"
          label="Create Job Card"
          icon="add_task"
          color="primary"
          outline
          @click="showJobCardDialog = true"
          size="sm"
          class="col-12 col-sm-auto"
        />
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

      <!-- Cost Structure Card -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Cost Structure</div>
              </div>
              <div class="col-auto">
                <q-btn
                  flat
                  round
                  dense
                  icon="refresh"
                  @click="loadCostStructures"
                  :loading="loadingCostStructures"
                />
              </div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div v-if="loadingCostStructures" class="text-center q-pa-sm">
              <q-spinner size="sm" color="primary" />
            </div>

            <!-- Has linked cost structure -->
            <div v-else-if="linkedCostStructure">
              <div class="q-gutter-sm">
                <div><strong>{{ linkedCostStructure.name }}</strong></div>
                <div v-if="linkedCostStructure.deposit_amount">
                  <strong>Deposit:</strong> {{ linkedCostStructure.deposit_amount }}
                </div>
                <div v-if="linkedCostStructure.components && linkedCostStructure.components.length">
                  <strong>Components:</strong>
                  <q-list dense class="q-ml-sm">
                    <q-item v-for="comp in linkedCostStructure.components" :key="comp.component_name" dense class="q-px-none" style="min-height: 24px">
                      <q-item-section>
                        <q-item-label class="text-body2">{{ comp.component_name }} — {{ comp.rate }} ({{ comp.unit_type }})</q-item-label>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </div>
                <div v-if="linkedDurationSummary">
                  <strong>Duration Options:</strong> {{ linkedDurationSummary }}
                </div>
              </div>
              <div class="q-mt-sm q-gutter-sm" v-if="authStore.isAdmin">
                <q-btn
                  flat
                  dense
                  label="Change"
                  icon="swap_horiz"
                  color="primary"
                  size="sm"
                  @click="csMode = 'select'"
                />
              </div>
            </div>

            <!-- No linked cost structure -->
            <div v-else>
              <div v-if="csMode === 'none'" class="text-center q-gutter-sm">
                <div class="text-grey-7 q-mb-sm">No cost structure linked</div>
                <div v-if="authStore.isAdmin" class="q-gutter-sm">
                  <q-btn
                    outline
                    dense
                    label="Select Existing"
                    icon="list"
                    color="primary"
                    size="sm"
                    @click="csMode = 'select'"
                  />
                  <q-btn
                    outline
                    dense
                    label="Create New"
                    icon="add"
                    color="primary"
                    size="sm"
                    @click="csMode = 'create'"
                  />
                </div>
              </div>

              <!-- Select existing -->
              <div v-if="csMode === 'select'">
                <q-select
                  v-model="csSelectedId"
                  :options="availableCostStructures"
                  :option-value="cs => cs.structure_id"
                  :option-label="cs => cs.name"
                  emit-value
                  map-options
                  label="Select Cost Structure"
                  outlined
                  dense
                  :loading="loadingCostStructures"
                >
                  <template v-slot:option="scope">
                    <q-item v-bind="scope.itemProps">
                      <q-item-section>
                        <q-item-label>{{ scope.opt.name }}</q-item-label>
                        <q-item-label caption v-if="scope.opt.components && scope.opt.components.length">
                          {{ scope.opt.components.map(c => c.component_name).join(', ') }}
                        </q-item-label>
                        <q-item-label caption>
                          {{ scope.opt.item_type === 'pue_type' ? 'Shared type structure — will link' : 'Item-specific — will clone for this item' }}
                        </q-item-label>
                      </q-item-section>
                    </q-item>
                  </template>
                </q-select>
                <div class="row justify-end q-mt-sm q-gutter-sm">
                  <q-btn flat dense label="Cancel" size="sm" @click="csMode = 'none'" />
                  <q-btn
                    dense
                    :label="selectedCsIsItemType ? 'Clone & Link' : 'Link'"
                    color="primary"
                    size="sm"
                    :disable="!csSelectedId"
                    :loading="csSaving"
                    @click="linkExistingStructure"
                  />
                </div>
              </div>

              <!-- Create new inline -->
              <div v-if="csMode === 'create'">
                <q-input
                  v-model="csNewForm.name"
                  label="Structure Name"
                  outlined
                  dense
                  class="q-mb-sm"
                />
                <q-input
                  v-model.number="csNewForm.deposit"
                  label="Deposit amount"
                  type="number"
                  step="0.01"
                  outlined
                  dense
                  class="q-mb-sm"
                />

                <div class="text-subtitle2">Components</div>
                <div
                  v-for="(comp, ci) in csNewForm.components"
                  :key="ci"
                  class="row q-col-gutter-xs items-center q-mb-xs"
                >
                  <div class="col-4">
                    <q-select
                      v-model="comp.unit_type"
                      :options="unitTypeOptions"
                      emit-value
                      map-options
                      label="Type"
                      outlined
                      dense
                      @update:model-value="onCsUnitTypeChange(comp)"
                    />
                    <q-input
                      v-if="comp.unit_type === 'custom'"
                      v-model="comp.custom_unit_type"
                      label="Custom unit (e.g. per_litre)"
                      outlined
                      dense
                      class="q-mt-xs"
                      @update:model-value="onCsCustomUnitChange(comp)"
                    />
                  </div>
                  <div class="col-4">
                    <q-input v-model="comp.component_name" label="Name" outlined dense />
                  </div>
                  <div class="col-3">
                    <q-input v-model.number="comp.rate" label="Rate" type="number" step="0.01" outlined dense />
                  </div>
                  <div class="col-1">
                    <q-btn flat round dense icon="close" color="negative" size="xs" @click="csNewForm.components.splice(ci, 1)" :disable="csNewForm.components.length <= 1" />
                  </div>
                </div>
                <q-btn flat dense icon="add" label="Add Component" color="primary" size="sm" @click="csAddComponent" class="q-mb-sm" />

                <div class="text-subtitle2">Duration Choices</div>
                <div
                  v-for="(ch, di) in csNewForm.durationChoices"
                  :key="di"
                  class="row q-col-gutter-xs items-center q-mb-xs"
                >
                  <div class="col-3">
                    <q-input v-model.number="ch.value" label="Value" type="number" min="1" outlined dense />
                  </div>
                  <div class="col-3">
                    <q-select v-model="ch.unit" :options="durationUnitOptions" emit-value map-options label="Unit" outlined dense />
                  </div>
                  <div class="col">
                    <q-input v-model="ch.label" label="Label" outlined dense />
                  </div>
                  <div class="col-1">
                    <q-btn flat round dense icon="close" color="negative" size="xs" @click="csNewForm.durationChoices.splice(di, 1)" :disable="csNewForm.durationChoices.length <= 1" />
                  </div>
                </div>
                <q-btn flat dense icon="add" label="Add Duration" color="primary" size="sm" @click="csAddDurationChoice" />

                <div class="row justify-end q-mt-sm q-gutter-sm">
                  <q-btn flat dense label="Cancel" size="sm" @click="csMode = 'none'" />
                  <q-btn
                    dense
                    label="Create & Link"
                    color="primary"
                    size="sm"
                    :disable="!csNewForm.name"
                    :loading="csSaving"
                    @click="createAndLinkStructure"
                  />
                </div>
              </div>
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

            <q-select
              v-model="editForm.pue_type_id"
              :options="pueTypeOptions"
              option-value="type_id"
              option-label="type_name"
              emit-value
              map-options
              label="Equipment Type"
              outlined
              clearable
              hint="Optional - categorize this equipment"
            >
              <template v-slot:prepend>
                <q-icon name="category" />
              </template>
            </q-select>

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

    <!-- Create Job Card Dialog -->
    <JobCardDialog
      v-model="showJobCardDialog"
      :linked-entity-type="'pue'"
      :linked-entity-id="pue?.pue_id"
      @saved="onJobCardSaved"
    />
  </q-page>
</template>

<script setup>
import { ref, inject, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { pueAPI, pueInspectionsAPI, pueRentalsAPI, settingsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'
import JobCardDialog from 'src/components/JobCardDialog.vue'
import { formatDateWithTimezone } from 'src/utils/dateFormat'

const $q = useQuasar()
const route = useRoute()
const authStore = useAuthStore()
const networkState = inject('networkState', { online: ref(true) })
const isOffline = computed(() => !networkState.online.value)

const pue = ref(null)
const loading = ref(true)
const inspections = ref([])
const loadingInspections = ref(false)
const rentalHistory = ref([])
const showRecordInspectionDialog = ref(false)
const showEditDialog = ref(false)
const showJobCardDialog = ref(false)
const savingInspection = ref(false)
const saving = ref(false)
const pueTypeOptions = ref([])

// Cost structure state
const allCostStructures = ref([])
const loadingCostStructures = ref(false)
const csMode = ref('none') // 'none', 'select', 'create'
const csSelectedId = ref(null)
const csSaving = ref(false)
const csNewForm = ref({
  name: '',
  deposit: null,
  components: [{ component_name: 'Daily Rate', unit_type: 'per_day', rate: null, is_calculated_on_return: false, sort_order: 0 }],
  durationChoices: [{ value: 1, unit: 'days', label: '1 Day' }]
})

const unitTypeOptions = [
  { label: 'Per Day', value: 'per_day' },
  { label: 'Per Week', value: 'per_week' },
  { label: 'Per Month', value: 'per_month' },
  { label: 'Per Hour', value: 'per_hour' },
  { label: 'Per kWh', value: 'per_kwh' },
  { label: 'Per Kg', value: 'per_kg' },
  { label: 'Per Litre', value: 'per_litre' },
  { label: 'Per Unit', value: 'per_unit' },
  { label: 'Per Recharge', value: 'per_recharge' },
  { label: 'One Time', value: 'one_time' },
  { label: 'Fixed Fee', value: 'fixed' },
  { label: 'Custom...', value: 'custom' }
]

const durationUnitOptions = [
  { label: 'Hours', value: 'hours' },
  { label: 'Days', value: 'days' },
  { label: 'Weeks', value: 'weeks' },
  { label: 'Months', value: 'months' }
]

const csUnitTypeLabels = {
  'per_day': 'Daily Rate',
  'per_week': 'Weekly Rate',
  'per_month': 'Monthly Rate',
  'per_hour': 'Hourly Rate',
  'per_kwh': 'kWh Usage',
  'per_kg': 'Weight Charge',
  'per_litre': 'Volume Charge',
  'per_unit': 'Per Unit',
  'per_recharge': 'Recharge Fee',
  'one_time': 'One-Time Fee',
  'fixed': 'Fixed Fee'
}

const linkedCostStructure = computed(() => {
  if (!pue.value) return null
  const pueId = pue.value.pue_id
  return allCostStructures.value.find(cs =>
    cs.pue_item_ids && cs.pue_item_ids.includes(pueId)
  ) || null
})

const availableCostStructures = computed(() => {
  return allCostStructures.value.filter(cs =>
    (cs.item_type === 'pue_item' || cs.item_type === 'pue_type') && cs.is_active !== false
  )
})

const selectedCsIsItemType = computed(() => {
  if (!csSelectedId.value) return false
  const cs = allCostStructures.value.find(c => c.structure_id === csSelectedId.value)
  return cs && cs.item_type === 'pue_item'
})

const linkedDurationSummary = computed(() => {
  const cs = linkedCostStructure.value
  if (!cs || !cs.duration_options || cs.duration_options.length === 0) return null
  const opt = cs.duration_options[0]
  const choices = opt.dropdown_choices || opt.dropdown_options || []
  const parsed = typeof choices === 'string' ? JSON.parse(choices) : choices
  if (parsed && parsed.length > 0) {
    return parsed.map(ch => ch.label).join(', ')
  }
  return null
})

const onCsUnitTypeChange = (component) => {
  const standardNames = Object.values(csUnitTypeLabels)
  if (!component.component_name || standardNames.includes(component.component_name)) {
    component.component_name = csUnitTypeLabels[component.unit_type] || ''
  }
  if (component.unit_type !== 'custom') {
    component.custom_unit_type = undefined
  }
}

const onCsCustomUnitChange = (component) => {
  if (component.custom_unit_type) {
    const label = component.custom_unit_type
      .replace(/^per_/, 'Per ')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase())
    const standardNames = Object.values(csUnitTypeLabels)
    if (!component.component_name || standardNames.includes(component.component_name) || component.component_name === label) {
      component.component_name = label
    }
  }
}

const csAddComponent = () => {
  csNewForm.value.components.push({
    component_name: 'Daily Rate',
    unit_type: 'per_day',
    rate: 0,
    is_calculated_on_return: false,
    sort_order: csNewForm.value.components.length
  })
}

const csAddDurationChoice = () => {
  csNewForm.value.durationChoices.push({ value: 1, unit: 'days', label: '1 Day' })
}

const loadCostStructures = async () => {
  if (!pue.value?.hub_id) return
  loadingCostStructures.value = true
  try {
    const response = await settingsAPI.getCostStructures({ hub_id: pue.value.hub_id })
    allCostStructures.value = response.data?.cost_structures || []
  } catch (error) {
    console.error('Failed to load cost structures:', error)
  } finally {
    loadingCostStructures.value = false
  }
}

const linkExistingStructure = async () => {
  if (!csSelectedId.value || !pue.value) return
  csSaving.value = true
  try {
    const sourceCs = allCostStructures.value.find(c => c.structure_id === csSelectedId.value)

    if (sourceCs && sourceCs.item_type === 'pue_item') {
      // Clone: create a new structure based on this one, for this specific PUE item
      const components = (sourceCs.components || []).map((c, i) => ({
        component_name: c.component_name,
        unit_type: c.unit_type,
        rate: c.rate || 0,
        is_calculated_on_return: c.is_calculated_on_return || false,
        sort_order: i
      }))
      const durationOptions = sourceCs.duration_options && sourceCs.duration_options.length > 0
        ? sourceCs.duration_options
        : undefined

      await settingsAPI.createCostStructure({
        hub_id: pue.value.hub_id,
        name: `${sourceCs.name} (${pue.value.name || pue.value.pue_id})`,
        item_type: 'pue_item',
        item_reference: pue.value.pue_id,
        components: JSON.stringify(components),
        duration_options: durationOptions ? JSON.stringify(durationOptions) : undefined,
        deposit_amount: sourceCs.deposit_amount || 0,
        pue_item_ids: JSON.stringify([pue.value.pue_id])
      })
      $q.notify({ type: 'positive', message: 'Cost structure cloned and linked', position: 'top' })
    } else {
      // Shared type structure: just add this PUE item to it
      await settingsAPI.addPUEItemToStructure(csSelectedId.value, pue.value.pue_id)
      $q.notify({ type: 'positive', message: 'Cost structure linked', position: 'top' })
    }

    csMode.value = 'none'
    csSelectedId.value = null
    await loadCostStructures()
  } catch (error) {
    console.error('Failed to link cost structure:', error)
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Failed to link cost structure', position: 'top' })
  } finally {
    csSaving.value = false
  }
}

const createAndLinkStructure = async () => {
  if (!csNewForm.value.name || !pue.value) return
  csSaving.value = true
  try {
    const components = csNewForm.value.components.map((c, i) => ({
      component_name: c.component_name,
      unit_type: c.unit_type === 'custom' && c.custom_unit_type ? c.custom_unit_type : c.unit_type,
      rate: c.rate || 0,
      is_calculated_on_return: c.is_calculated_on_return || false,
      sort_order: i
    }))
    const durationOptions = csNewForm.value.durationChoices.length > 0 ? [{
      input_type: 'dropdown',
      label: 'Rental Duration',
      custom_unit: 'days',
      dropdown_options: JSON.stringify(csNewForm.value.durationChoices.map(ch => ({
        value: ch.value,
        unit: ch.unit,
        label: ch.label
      }))),
      sort_order: 0
    }] : undefined

    await settingsAPI.createCostStructure({
      hub_id: pue.value.hub_id,
      name: csNewForm.value.name,
      item_type: 'pue_item',
      item_reference: pue.value.pue_id,
      components: JSON.stringify(components),
      duration_options: durationOptions ? JSON.stringify(durationOptions) : undefined,
      deposit_amount: csNewForm.value.deposit || 0,
      pue_item_ids: JSON.stringify([pue.value.pue_id])
    })

    $q.notify({ type: 'positive', message: 'Cost structure created and linked', position: 'top' })
    csMode.value = 'none'
    csNewForm.value = {
      name: '',
      deposit: null,
      components: [{ component_name: 'Daily Rate', unit_type: 'per_day', rate: null, is_calculated_on_return: false, sort_order: 0 }],
      durationChoices: [{ value: 1, unit: 'days', label: '1 Day' }]
    }
    await loadCostStructures()
  } catch (error) {
    console.error('Failed to create cost structure:', error)
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Failed to create cost structure', position: 'top' })
  } finally {
    csSaving.value = false
  }
}

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
  status: 'available',
  pue_type_id: null
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

const formatDate = (dateStr) => formatDateWithTimezone(dateStr, 'short')

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
    console.log('[PUEDetailPage] Loading PUE with ID:', pueId)
    const response = await pueAPI.get(pueId)
    console.log('[PUEDetailPage] PUE response:', response.data)
    pue.value = response.data

    // Load inspections, rental history, and cost structures
    await Promise.all([loadInspections(), loadRentalHistory(), loadCostStructures()])
  } catch (error) {
    console.error('[PUEDetailPage] Failed to load PUE:', error)
    console.error('[PUEDetailPage] Error details:', error.response?.data)
    if (navigator.onLine) {
      $q.notify({
        type: 'negative',
        message: 'Failed to load equipment details',
        position: 'top'
      })
    }
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
    if (navigator.onLine) {
      $q.notify({
        type: 'negative',
        message: 'Failed to load inspections',
        position: 'top'
      })
    }
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
    if (!isOffline.value) {
      $q.notify({
        type: 'negative',
        message: error.response?.data?.detail || 'Failed to record inspection',
        position: 'top'
      })
    }
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

const editPUE = async () => {
  // Load PUE types for the hub
  if (pue.value.hub_id) {
    try {
      const response = await settingsAPI.getPUETypes(pue.value.hub_id)
      pueTypeOptions.value = response.data?.pue_types || []
    } catch (error) {
      console.error('Failed to load PUE types:', error)
    }
  }

  editForm.value = {
    name: pue.value.name,
    description: pue.value.description || '',
    power_rating_watts: pue.value.power_rating_watts,
    usage_location: pue.value.usage_location || 'both',
    storage_location: pue.value.storage_location || '',
    status: pue.value.status,
    pue_type_id: pue.value.pue_type_id
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
    if (!isOffline.value) {
      $q.notify({
        type: 'negative',
        message: error.response?.data?.detail || 'Failed to update equipment',
        position: 'top'
      })
    }
  } finally {
    saving.value = false
  }
}

const onJobCardSaved = () => {
  $q.notify({
    type: 'positive',
    message: 'Job card created successfully',
    position: 'top'
  })
  showJobCardDialog.value = false
}

onMounted(() => {
  loadPUE()
})
</script>
