<template>
  <q-card>
    <q-card-section>
      <div class="text-h6 q-mb-md">
        <slot name="title">Battery Rental Information</slot>
      </div>

      <div class="row q-col-gutter-md">
        <!-- Hub Selection (only for superadmin) -->
        <div v-if="authStore.role === 'superadmin'" class="col-12">
          <q-select
            v-model="formData.hub_id"
            :options="hubOptions"
            option-value="hub_id"
            option-label="what_three_word_location"
            emit-value
            map-options
            label="Hub *"
            outlined
            :rules="[val => !!val || 'Hub is required']"
            @update:model-value="onHubChange"
          >
            <template v-slot:prepend>
              <q-icon name="store" />
            </template>
          </q-select>
        </div>

        <!-- Customer Selection -->
        <div class="col-12 col-md-6">
          <q-select
            v-model="formData.user"
            :options="userOptions"
            option-value="user_id"
            option-label="Name"
            label="Select Customer *"
            outlined
            use-input
            input-debounce="300"
            @filter="filterUsers"
            :loading="usersLoading"
            :rules="[val => !!val || 'Customer is required']"
            :disable="!formData.hub_id"
            :hint="!formData.hub_id ? 'Select a hub first' : ''"
          >
            <template v-slot:prepend>
              <q-icon name="person" />
            </template>
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.Name || scope.opt.username }}</q-item-label>
                  <q-item-label caption>ID: {{ scope.opt.user_id }} | Mobile: {{ scope.opt.mobile_number || 'N/A' }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  No users found
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>

        <!-- Cost Structure Selection (shown below customer) -->
        <div class="col-12">
          <q-select
            v-model="formData.costStructure"
            :options="costStructureOptions"
            option-label="name"
            label="Cost Structure *"
            outlined
            :loading="costStructuresLoading"
            :rules="[val => !!val || 'Cost structure is required']"
            :disable="!formData.hub_id"
            :hint="!formData.hub_id ? 'Select a hub first' : costStructureOptions.length === 0 ? `No cost structures available (Hub ID: ${formData.hub_id})` : `${costStructureOptions.length} cost structure(s) available`"
          >
            <template v-slot:prepend>
              <q-icon name="attach_money" />
            </template>
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.name }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>

        <!-- Battery Selection with Chips (MOVED BEFORE DURATION) -->
        <div v-if="formData.costStructure" class="col-12">
          <q-card flat bordered class="bg-blue-1">
            <q-card-section>
              <div class="text-subtitle2 q-mb-sm">Select Battery * (Single battery only)</div>
              <q-input
                v-model="batterySearchFilter"
                outlined
                dense
                placeholder="Search batteries..."
                class="q-mb-sm"
                :disable="!formData.hub_id"
                bg-color="white"
              >
                <template v-slot:prepend>
                  <q-icon name="search" />
                </template>
              </q-input>

              <div v-if="batteriesLoading" class="row justify-center q-pa-md">
                <q-spinner color="primary" size="2em" />
              </div>

              <div v-else-if="!formData.hub_id" class="text-grey-7 q-pa-md text-center">
                <q-icon name="info" size="48px" class="q-mb-sm" />
                <div>Select a hub first to see available batteries</div>
              </div>

              <div v-else-if="availableBatteries.length === 0" class="text-grey-7 q-pa-md text-center">
                <q-icon name="battery_unknown" size="48px" class="q-mb-sm" />
                <div>No available batteries found</div>
              </div>

              <div v-else class="q-gutter-sm">
                <q-chip
                  v-for="battery in filteredBatteries"
                  :key="battery.battery_id"
                  :selected="formData.battery_id === battery.battery_id"
                  clickable
                  color="primary"
                  text-color="white"
                  @click="selectBattery(battery.battery_id)"
                >
                  <q-avatar :icon="formData.battery_id === battery.battery_id ? 'radio_button_checked' : 'radio_button_unchecked'" />
                  Battery #{{ battery.battery_id }}
                  <span v-if="battery.short_id" class="q-ml-xs">({{ battery.short_id }})</span>
                  <span v-else-if="battery.model" class="q-ml-xs">({{ battery.model }})</span>
                </q-chip>
              </div>
              <div v-if="formData.battery_id" class="text-caption text-positive q-mt-sm">
                Battery #{{ formData.battery_id }} selected
              </div>
              <div v-else class="text-caption text-negative q-mt-sm">
                Please select one battery
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Rental Duration -->
        <div v-if="formData.costStructure && availableDurations.length > 0" class="col-12 col-md-6">
          <q-select
            v-model="formData.duration"
            :options="availableDurations"
            option-label="label"
            label="Rental Duration *"
            outlined
            :rules="[val => !!val || 'Rental duration is required']"
            @update:model-value="updateDueDate"
          >
            <template v-slot:prepend>
              <q-icon name="schedule" />
            </template>
          </q-select>
        </div>

        <!-- Custom Duration Input -->
        <div v-if="formData.costStructure && formData.costStructure.allow_custom_duration && formData.duration?.input_type === 'custom'" class="col-12 col-md-6">
          <q-input
            v-model.number="formData.customDurationValue"
            :label="`Custom ${formData.duration.label || 'Duration'} *`"
            outlined
            type="number"
            min="1"
            :rules="[val => val > 0 || 'Must be greater than 0']"
            @update:model-value="updateDueDate"
          >
            <template v-slot:prepend>
              <q-icon name="edit_calendar" />
            </template>
            <template v-slot:append>
              <span class="text-caption text-grey-7">{{ formData.duration.custom_unit }}</span>
            </template>
          </q-input>
        </div>

        <!-- Cost Estimate Display -->
        <div v-if="formData.costStructure && formData.duration" class="col-12">
          <q-card flat bordered class="bg-blue-1">
            <q-card-section>
              <div class="text-subtitle2 q-mb-sm">
                <q-icon name="calculate" class="q-mr-xs" />
                Cost Estimate
                <q-badge v-if="costEstimate?.has_estimated_component" color="orange" label="Estimated" class="q-ml-sm" />
              </div>

              <div v-if="costEstimateLoading" class="row justify-center q-pa-md">
                <q-spinner color="primary" size="2em" />
              </div>

              <div v-else-if="costEstimate">
                <!-- Cost Breakdown -->
                <div v-if="costEstimate.breakdown && costEstimate.breakdown.length > 0" class="q-mb-md">
                  <div class="text-caption text-grey-7 q-mb-xs">Breakdown:</div>
                  <div v-for="(component, idx) in costEstimate.breakdown" :key="idx" class="row justify-between q-py-xs text-body2">
                    <div class="col">
                      {{ component.component_name }}
                      <span class="text-caption text-grey-7">
                        ({{ component.rate }} per {{ component.unit_type }} × {{ component.quantity }})
                      </span>
                    </div>
                    <div class="col-auto text-weight-medium">
                      {{ component.amount.toFixed(2) }} XAF
                    </div>
                  </div>
                </div>

                <!-- Recurring Components Warning -->
                <q-banner v-if="recurringComponents.length > 0" dense class="bg-orange-2 text-orange-9 q-mb-sm" rounded>
                  <template v-slot:avatar>
                    <q-icon name="schedule" color="orange" />
                  </template>
                  <div class="text-caption">
                    <strong>Recurring Charges:</strong>
                    <div v-for="comp in recurringComponents" :key="comp.component_name">
                      {{ comp.rate }} XAF {{ formatUnitType(comp.unit_type) }}
                    </div>
                    These will be billed automatically via cron job.
                  </div>
                </q-banner>

                <!-- Totals -->
                <q-separator class="q-my-sm" />
                <div class="row justify-between text-body2">
                  <div class="col">Subtotal:</div>
                  <div class="col-auto text-weight-medium">{{ costEstimate.subtotal.toFixed(2) }} XAF</div>
                </div>
                <div v-if="costEstimate.vat > 0" class="row justify-between text-body2">
                  <div class="col">VAT ({{ costEstimate.vat_percentage }}%):</div>
                  <div class="col-auto text-weight-medium">{{ costEstimate.vat.toFixed(2) }} XAF</div>
                </div>
                <q-separator class="q-my-sm" />
                <div class="row justify-between text-h6 text-primary">
                  <div class="col">Total:</div>
                  <div class="col-auto">{{ costEstimate.total.toFixed(2) }} XAF</div>
                </div>
                <div v-if="costEstimate.deposit_amount > 0" class="row justify-between text-body2 text-grey-7 q-mt-xs">
                  <div class="col">Suggested Deposit:</div>
                  <div class="col-auto">{{ costEstimate.deposit_amount.toFixed(2) }} XAF</div>
                </div>
              </div>

              <div v-else class="text-caption text-grey-7">
                Select a duration to see cost estimate
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Rental Start Date -->
        <div class="col-12 col-md-6">
          <q-input
            v-model="formData.rentalStartDate"
            label="Rental Start Date"
            outlined
            type="datetime-local"
            :disable="authStore.role === 'hub_admin'"
            :hint="authStore.role === 'hub_admin' ? 'Automatically set to current date/time' : ''"
          >
            <template v-slot:prepend>
              <q-icon name="event" />
            </template>
          </q-input>
        </div>

        <!-- Due Date -->
        <div class="col-12 col-md-6">
          <q-input
            v-model="formData.dueDate"
            label="Due Date (Optional)"
            outlined
            type="datetime-local"
          >
            <template v-slot:prepend>
              <q-icon name="event_available" />
            </template>
          </q-input>
        </div>

        <!-- Deposit Amount -->
        <div class="col-12 col-md-6">
          <q-input
            v-model.number="formData.depositAmount"
            label="Deposit Amount (Optional)"
            outlined
            type="number"
            step="0.01"
            min="0"
          >
            <template v-slot:prepend>
              <q-icon name="account_balance_wallet" />
            </template>
            <template v-slot:append>
              <span>XAF</span>
            </template>
          </q-input>
        </div>

        <!-- Notes -->
        <div class="col-12">
          <q-input
            v-model="formData.notes"
            label="Notes (Optional)"
            outlined
            type="textarea"
            rows="3"
          >
            <template v-slot:prepend>
              <q-icon name="note" />
            </template>
          </q-input>
        </div>
      </div>
    </q-card-section>

    <q-card-actions align="right" class="q-px-md q-pb-md">
      <q-btn
        flat
        label="Cancel"
        color="grey"
        @click="$emit('cancel')"
      />
      <q-btn
        label="Create Rental"
        color="primary"
        icon="add"
        @click="handleSubmit"
        :loading="submitting"
        :disable="!isFormValid"
      />
    </q-card-actions>
  </q-card>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useQuasar, date } from 'quasar'
import { hubsAPI, batteriesAPI, settingsAPI, batteryRentalsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'

const $q = useQuasar()
const authStore = useAuthStore()

// Props & Emits
const emit = defineEmits(['submit', 'cancel', 'success', 'error'])

// Form Data
const formData = ref({
  hub_id: null,
  user: null,
  costStructure: null,
  duration: null,
  customDurationValue: 1,
  battery_id: null,
  rentalStartDate: new Date().toISOString().slice(0, 16),
  dueDate: null,
  depositAmount: 0,
  notes: ''
})

// Loading States
const usersLoading = ref(false)
const batteriesLoading = ref(false)
const costStructuresLoading = ref(false)
const submitting = ref(false)
const costEstimateLoading = ref(false)

// Data Options
const hubOptions = ref([])
const userOptions = ref([])
const allUsers = ref([])
const availableBatteries = ref([])
const costStructureOptions = ref([])
const costEstimate = ref(null)
const batterySearchFilter = ref('')

// Auto-select hub for admin and hub_admin
onMounted(async () => {
  try {
    await loadHubs()

    // Auto-select hub for admin/hub_admin
    if ((authStore.role === 'admin' || authStore.role === 'hub_admin') && authStore.currentHubId) {
      formData.value.hub_id = authStore.currentHubId
      // Explicitly load data since watcher doesn't fire on initial set
      await onHubChange()
    }
  } catch (error) {
    console.error('Error in onMounted:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to initialize form',
      position: 'top'
    })
  }
})

// Load Hubs
const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

// Hub Change Handler
const onHubChange = async () => {
  if (!formData.value.hub_id) return

  // Reset dependent fields
  formData.value.user = null
  formData.value.battery_id = null
  formData.value.costStructure = null

  // Load data for the selected hub
  try {
    await Promise.all([
      loadUsers(),
      loadBatteries(),
      loadCostStructures()
    ])
  } catch (error) {
    console.error('Error loading hub data:', error)
  }
}

// Load Users
const loadUsers = async () => {
  if (!formData.value.hub_id) return

  usersLoading.value = true
  try {
    const response = await hubsAPI.getUsers(formData.value.hub_id)
    allUsers.value = response.data || []
    userOptions.value = allUsers.value
  } catch (error) {
    console.error('Failed to load users:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load users',
      position: 'top'
    })
  } finally {
    usersLoading.value = false
  }
}

// Filter Users
const filterUsers = (val, update) => {
  if (val === '') {
    update(() => {
      userOptions.value = allUsers.value
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    userOptions.value = allUsers.value.filter(u =>
      (u.Name && u.Name.toLowerCase().includes(needle)) ||
      (u.username && u.username.toLowerCase().includes(needle)) ||
      (u.mobile_number && u.mobile_number.includes(needle))
    )
  })
}

// Load Batteries
const loadBatteries = async () => {
  if (!formData.value.hub_id) return

  batteriesLoading.value = true
  try {
    const response = await batteriesAPI.list({
      hub_id: formData.value.hub_id,
      status: 'available'
    })
    availableBatteries.value = response.data || []
  } catch (error) {
    console.error('Failed to load batteries:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load batteries',
      position: 'top'
    })
  } finally {
    batteriesLoading.value = false
  }
}

// Filtered Batteries (with search)
const filteredBatteries = computed(() => {
  if (!batterySearchFilter.value) return availableBatteries.value

  const needle = batterySearchFilter.value.toLowerCase()
  return availableBatteries.value.filter(b =>
    b.battery_id?.toString().includes(needle) ||
    b.short_id?.toLowerCase().includes(needle) ||
    b.model?.toLowerCase().includes(needle)
  )
})

// Select Battery
const selectBattery = (batteryId) => {
  formData.value.battery_id = batteryId
}

// Load Cost Structures
const loadCostStructures = async () => {
  if (!formData.value.hub_id) return

  costStructuresLoading.value = true
  try {
    const response = await settingsAPI.getCostStructures({
      hub_id: formData.value.hub_id
    })
    // Filter for battery type on the client side
    const allStructures = response.data?.cost_structures || response.data || []
    costStructureOptions.value = allStructures.filter(cs =>
      cs.item_type === 'battery' && cs.is_active !== false
    )
  } catch (error) {
    console.error('Failed to load cost structures:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load cost structures',
      position: 'top'
    })
  } finally {
    costStructuresLoading.value = false
  }
}

// Available Durations
const availableDurations = computed(() => {
  if (!formData.value.costStructure || !formData.value.costStructure.duration_options) {
    return []
  }

  const durationOptions = formData.value.costStructure.duration_options

  // Extract dropdown options if input_type is 'dropdown'
  if (durationOptions.length === 1 && durationOptions[0].input_type === 'dropdown') {
    const dropdownOpts = durationOptions[0].dropdown_options || []
    return dropdownOpts.map(opt => ({
      ...opt,
      label: opt.label,
      option_id: durationOptions[0].option_id,
      input_type: 'preset',
      default_value: opt.value,
      custom_unit: opt.unit
    }))
  }

  return durationOptions
})

// Recurring Components
const recurringComponents = computed(() => {
  if (!costEstimate.value?.breakdown) return []

  const recurringUnits = ['per_month', 'per_week', 'per_year', 'per_day']
  return costEstimate.value.breakdown.filter(c =>
    recurringUnits.includes(c.unit_type)
  )
})

// Format Unit Type
const formatUnitType = (unitType) => {
  const unitMap = {
    'per_month': 'monthly',
    'per_week': 'weekly',
    'per_year': 'yearly',
    'per_day': 'daily',
    'per_hour': 'hourly'
  }
  return unitMap[unitType] || unitType.replace('per_', '')
}

// Update Due Date based on duration
const updateDueDate = () => {
  if (!formData.value.duration || !formData.value.rentalStartDate) return

  const startDate = new Date(formData.value.rentalStartDate)
  let durationValue = formData.value.duration.input_type === 'custom'
    ? formData.value.customDurationValue
    : formData.value.duration.default_value

  let durationUnit = formData.value.duration.custom_unit || 'days'

  const addOptions = {}
  if (durationUnit === 'days') addOptions.days = durationValue
  else if (durationUnit === 'hours') addOptions.hours = durationValue
  else if (durationUnit === 'weeks') addOptions.days = durationValue * 7
  else if (durationUnit === 'months') addOptions.months = durationValue

  const dueDate = date.addToDate(startDate, addOptions)
  formData.value.dueDate = date.formatDate(dueDate, 'YYYY-MM-DDTHH:mm')

  // Recalculate cost estimate
  calculateCostEstimate()
}

// Calculate Cost Estimate
const calculateCostEstimate = async () => {
  if (!formData.value.costStructure || !formData.value.duration) {
    costEstimate.value = null
    return
  }

  const durationValue = formData.value.duration.input_type === 'custom'
    ? formData.value.customDurationValue
    : formData.value.duration.default_value

  if (!durationValue || durationValue <= 0) {
    costEstimate.value = null
    return
  }

  costEstimateLoading.value = true
  try {
    const response = await settingsAPI.estimateCost(
      formData.value.costStructure.cost_structure_id || formData.value.costStructure.structure_id,
      {
        duration_value: durationValue,
        duration_unit: formData.value.duration.custom_unit || 'days',
        vat_percentage: 0
      }
    )
    costEstimate.value = response.data
  } catch (error) {
    console.error('Failed to calculate cost estimate:', error)
  } finally {
    costEstimateLoading.value = false
  }
}

// Form Validation
const isFormValid = computed(() => {
  return formData.value.hub_id &&
         formData.value.user &&
         formData.value.costStructure &&
         formData.value.duration &&
         formData.value.battery_id
})

// Watch for hub_id changes
watch(() => formData.value.hub_id, async (newHubId, oldHubId) => {
  if (newHubId && newHubId !== oldHubId) {
    await onHubChange()
  }
})

// Watch for cost structure or duration changes
watch([() => formData.value.costStructure, () => formData.value.duration], () => {
  if (formData.value.costStructure && formData.value.duration) {
    updateDueDate()
  }
})

// Handle Submit
const handleSubmit = async () => {
  if (!isFormValid.value) {
    $q.notify({
      type: 'warning',
      message: 'Please fill in all required fields',
      position: 'top'
    })
    return
  }

  submitting.value = true
  try {
    const rentalData = {
      user_id: formData.value.user.user_id,
      battery_ids: [formData.value.battery_id.toString()], // Backend expects array of strings
      cost_structure_id: formData.value.costStructure.cost_structure_id || formData.value.costStructure.structure_id,
      rental_start_date: formData.value.rentalStartDate ? new Date(formData.value.rentalStartDate).toISOString() : undefined,
      due_date: formData.value.dueDate ? new Date(formData.value.dueDate).toISOString() : undefined,
      deposit_amount: formData.value.depositAmount > 0 ? formData.value.depositAmount : undefined,
      notes: formData.value.notes ? [formData.value.notes] : undefined
    }

    const response = await batteryRentalsAPI.create(rentalData)

    $q.notify({
      type: 'positive',
      message: 'Battery rental created successfully!',
      position: 'top'
    })

    emit('success', response.data)
  } catch (error) {
    console.error('Failed to create rental:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create rental',
      position: 'top'
    })
    emit('error', error)
  } finally {
    submitting.value = false
  }
}
</script>
