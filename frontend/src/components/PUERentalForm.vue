<template>
  <q-card>
    <q-card-section>
      <div class="text-h6 q-mb-md">
        <slot name="title">PUE Rental Information</slot>
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
            :hint="!formData.hub_id ? 'Select a hub first' : costStructureOptions.length === 0 ? 'No cost structures available for this hub' : ''"
          >
            <template v-slot:prepend>
              <q-icon name="attach_money" />
            </template>
            <template v-slot:option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.name }}</q-item-label>
                  <q-item-label caption>
                    {{ scope.opt.description }}
                    <q-badge v-if="scope.opt.is_pay_to_own" color="purple" label="Pay to Own" class="q-ml-xs" />
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>

        <!-- PUE Item Selection with Chips (MOVED BEFORE DURATION) -->
        <div v-if="formData.costStructure" class="col-12">
          <q-card flat bordered class="bg-blue-1">
            <q-card-section>
              <div class="text-subtitle2 q-mb-sm">Select PUE Item *</div>
              <q-input
                v-model="pueSearchFilter"
                outlined
                dense
                placeholder="Search PUE items..."
                class="q-mb-sm"
                :disable="!formData.hub_id || !formData.costStructure"
                bg-color="white"
              >
                <template v-slot:prepend>
                  <q-icon name="search" />
                </template>
              </q-input>

              <div v-if="pueLoading" class="row justify-center q-pa-md">
                <q-spinner color="primary" size="2em" />
              </div>

              <div v-else-if="!formData.hub_id" class="text-grey-7 q-pa-md text-center">
                <q-icon name="info" size="48px" class="q-mb-sm" />
                <div>Select a hub first to see available PUE items</div>
              </div>

              <div v-else-if="!formData.costStructure" class="text-grey-7 q-pa-md text-center">
                <q-icon name="info" size="48px" class="q-mb-sm" />
                <div>Select a cost structure to see matching PUE items</div>
              </div>

              <div v-else-if="availablePUEs.length === 0" class="text-grey-7 q-pa-md text-center">
                <q-icon name="devices_other" size="48px" class="q-mb-sm" />
                <div>No available PUE items found for this cost structure</div>
              </div>

              <div v-else class="q-gutter-sm">
                <q-chip
                  v-for="pue in filteredPUEs"
                  :key="pue.pue_id"
                  :selected="formData.pue_id === pue.pue_id"
                  clickable
                  color="purple"
                  text-color="white"
                  @click="selectPUE(pue.pue_id)"
                >
                  <q-avatar :icon="formData.pue_id === pue.pue_id ? 'radio_button_checked' : 'radio_button_unchecked'" />
                  PUE #{{ pue.pue_id }}
                  <span v-if="pue.name" class="q-ml-xs">({{ pue.name }})</span>
                </q-chip>
              </div>
              <div v-if="formData.pue_id" class="text-caption text-positive q-mt-sm">
                PUE #{{ formData.pue_id }} selected
              </div>
              <div v-else class="text-caption text-negative q-mt-sm">
                Please select one PUE item
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Pay-to-Own Banner -->
        <template v-if="isPayToOwn">
          <div class="col-12">
            <q-banner class="bg-purple-1 text-purple-9" rounded>
              <template v-slot:avatar>
                <q-icon name="account_balance" color="purple" />
              </template>
              <div class="text-h6">Pay to Own</div>
              <div class="text-body2">
                Total Item Cost: XAF {{ formData.costStructure.item_total_cost?.toFixed(2) || '0.00' }}
              </div>

              <div v-if="recurringCostComponent" class="text-body2 q-mt-sm">
                <q-icon name="calendar_month" size="sm" class="q-mr-xs" />
                <strong>{{ recurringCostComponent.rate }} XAF per {{ formatUnitType(recurringCostComponent.unit_type) }}</strong>
              </div>

              <div class="text-caption q-mt-xs">
                This rental will allow the customer to gradually own this item through payments.
              </div>

              <q-banner v-if="recurringCostComponent" dense class="bg-orange-2 text-orange-9 q-mt-sm" rounded>
                <template v-slot:avatar>
                  <q-icon name="schedule" color="orange" size="sm" />
                </template>
                <div class="text-caption">
                  <strong>Automatic Billing:</strong> Customer will be automatically billed {{ recurringCostComponent.rate }} XAF {{ formatUnitType(recurringCostComponent.unit_type) }} via the cron job until the item is fully paid.
                </div>
              </q-banner>
            </q-banner>
          </div>

          <!-- Payment Schedule for Pay-to-Own -->
          <div v-if="paymentSchedule" class="col-12">
            <q-card bordered flat class="bg-blue-1">
              <q-card-section>
                <div class="text-subtitle1 text-weight-medium q-mb-sm">
                  <q-icon name="event_note" class="q-mr-xs" />
                  Recurring Payment Schedule
                </div>

                <div class="q-gutter-sm">
                  <div class="row items-center">
                    <div class="col-6 text-body2">Total Item Cost:</div>
                    <div class="col-6 text-right text-weight-medium">XAF {{ paymentSchedule.totalCost.toFixed(2) }}</div>
                  </div>

                  <div v-if="paymentSchedule.initialPayment > 0" class="row items-center">
                    <div class="col-6 text-body2">Initial Payment:</div>
                    <div class="col-6 text-right text-weight-medium text-green">- XAF {{ paymentSchedule.initialPayment.toFixed(2) }}</div>
                  </div>

                  <q-separator />

                  <div class="row items-center">
                    <div class="col-6 text-body2">Remaining Balance:</div>
                    <div class="col-6 text-right text-weight-bold">XAF {{ paymentSchedule.remainingBalance.toFixed(2) }}</div>
                  </div>

                  <div class="row items-center">
                    <div class="col-6 text-body2">Payment Frequency:</div>
                    <div class="col-6 text-right text-weight-medium">XAF {{ paymentSchedule.recurringRate.toFixed(2) }} per {{ formatUnitType(paymentSchedule.unitType) }}</div>
                  </div>

                  <div class="row items-center">
                    <div class="col-6 text-body2">Number of Payments:</div>
                    <div class="col-6 text-right text-weight-medium">{{ paymentSchedule.numberOfPayments }} payments</div>
                  </div>

                  <div class="row items-center">
                    <div class="col-6 text-body2">Time to Pay Off:</div>
                    <div class="col-6 text-right text-weight-medium">{{ paymentSchedule.totalTime }} {{ paymentSchedule.timeUnit }}</div>
                  </div>
                </div>

                <q-banner dense class="bg-info text-white q-mt-md" rounded>
                  <template v-slot:avatar>
                    <q-icon name="info" />
                  </template>
                  <div class="text-caption">
                    The customer will be automatically charged <strong>XAF {{ paymentSchedule.recurringRate.toFixed(2) }}</strong> {{ formatUnitType(paymentSchedule.unitType) }} until the item is fully paid off.
                  </div>
                </q-banner>
              </q-card-section>
            </q-card>
          </div>

          <!-- Initial Payment for Pay-to-Own -->
          <div class="col-12">
            <q-input
              v-model.number="formData.initialPayment"
              label="Initial Payment (Optional)"
              outlined
              type="number"
              step="0.01"
              min="0"
              :max="formData.costStructure.item_total_cost"
              hint="Amount paid upfront towards ownership"
            >
              <template v-slot:prepend>
                <q-icon name="account_balance_wallet" />
              </template>
              <template v-slot:append>
                <span>XAF</span>
              </template>
            </q-input>
          </div>
        </template>

        <!-- Regular Rental Options (not pay-to-own) -->
        <template v-if="!isPayToOwn && formData.costStructure">
          <!-- Rental Duration -->
          <div v-if="availableDurations.length > 0" class="col-12 col-md-6">
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
          <div v-if="formData.costStructure.allow_custom_duration && formData.duration?.input_type === 'custom'" class="col-12 col-md-6">
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

          <!-- Recurring Payment Toggle -->
          <div v-if="hasRecurringComponents" class="col-12">
            <q-card bordered flat class="bg-orange-1">
              <q-card-section>
                <div class="row items-center">
                  <div class="col">
                    <div class="text-subtitle2">
                      <q-icon name="autorenew" class="q-mr-xs" />
                      Enable Recurring Payment
                    </div>
                    <div class="text-caption text-grey-8">
                      Customer can opt to pay regularly via automatic billing, or return and rent again each time
                    </div>
                  </div>
                  <div class="col-auto">
                    <q-toggle
                      v-model="formData.enableRecurring"
                      color="orange"
                      size="lg"
                    />
                  </div>
                </div>

                <div v-if="formData.enableRecurring && recurringCostComponent" class="q-mt-md">
                  <q-banner dense class="bg-orange-2 text-orange-9" rounded>
                    <template v-slot:avatar>
                      <q-icon name="schedule" color="orange" />
                    </template>
                    <div class="text-caption">
                      <strong>Automatic Billing:</strong> Customer will be billed {{ recurringCostComponent.rate }} XAF {{ formatUnitType(recurringCostComponent.unit_type) }} via cron job
                    </div>
                  </q-banner>
                </div>
              </q-card-section>
            </q-card>
          </div>

          <!-- Cost Estimate for Regular Rentals -->
          <div v-if="formData.duration" class="col-12">
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
                </div>

                <div v-else class="text-caption text-grey-7">
                  Select a duration to see cost estimate
                </div>
              </q-card-section>
            </q-card>
          </div>
        </template>

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
        :label="isPayToOwn ? 'Create Pay-to-Own Rental' : 'Create Rental'"
        :color="isPayToOwn ? 'purple' : 'primary'"
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
import { hubsAPI, pueAPI, settingsAPI, pueRentalsAPI } from 'src/services/api'
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
  pue_id: null,
  rentalStartDate: new Date().toISOString().slice(0, 16),
  initialPayment: 0,
  enableRecurring: false,
  notes: ''
})

// Loading States
const usersLoading = ref(false)
const pueLoading = ref(false)
const costStructuresLoading = ref(false)
const submitting = ref(false)
const costEstimateLoading = ref(false)

// Data Options
const hubOptions = ref([])
const userOptions = ref([])
const allUsers = ref([])
const availablePUEs = ref([])
const costStructureOptions = ref([])
const costEstimate = ref(null)
const pueSearchFilter = ref('')

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

  formData.value.user = null
  formData.value.pue_id = null
  formData.value.costStructure = null

  try {
    await Promise.all([
      loadUsers(),
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

// Load Cost Structures
const loadCostStructures = async () => {
  if (!formData.value.hub_id) return

  costStructuresLoading.value = true
  try {
    const response = await settingsAPI.getCostStructures({
      hub_id: formData.value.hub_id
    })
    // Filter for PUE type on the client side
    const allStructures = response.data?.cost_structures || response.data || []
    costStructureOptions.value = allStructures.filter(cs =>
      cs.item_type === 'pue_item' && cs.is_active !== false
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

// Watch cost structure to load PUEs
watch(() => formData.value.costStructure, async (newVal) => {
  if (newVal) {
    await loadPUEs()
  } else {
    availablePUEs.value = []
  }
})

// Load PUE Items
const loadPUEs = async () => {
  if (!formData.value.hub_id) return

  pueLoading.value = true
  try {
    const response = await hubsAPI.getAvailablePUE(formData.value.hub_id)
    let pues = response.data || []

    // Filter by cost structure's item_reference
    if (formData.value.costStructure?.item_reference && formData.value.costStructure.item_reference !== 'all') {
      const itemRef = formData.value.costStructure.item_reference
      pues = pues.filter(p => {
        return p.pue_id?.toString() === itemRef ||
               p.pue_type_id?.toString() === itemRef ||
               p.reference?.toString() === itemRef
      })
    }

    availablePUEs.value = pues
  } catch (error) {
    console.error('Failed to load PUE items:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load PUE items',
      position: 'top'
    })
  } finally {
    pueLoading.value = false
  }
}

// Filtered PUEs (with search)
const filteredPUEs = computed(() => {
  if (!pueSearchFilter.value) return availablePUEs.value

  const needle = pueSearchFilter.value.toLowerCase()
  return availablePUEs.value.filter(p =>
    p.pue_id?.toString().includes(needle) ||
    p.name?.toLowerCase().includes(needle) ||
    p.pue_type_name?.toLowerCase().includes(needle)
  )
})

// Select PUE
const selectPUE = (pueId) => {
  formData.value.pue_id = pueId
}

// Check if pay-to-own
const isPayToOwn = computed(() => {
  if (!formData.value.costStructure) return false
  return formData.value.costStructure.is_pay_to_own || false
})

// Get recurring cost component
const recurringCostComponent = computed(() => {
  if (!formData.value.costStructure?.cost_components) return null

  const recurringUnits = ['per_month', 'per_week', 'per_year', 'per_day']
  return formData.value.costStructure.cost_components.find(c =>
    recurringUnits.includes(c.unit_type)
  )
})

// Check if has recurring components
const hasRecurringComponents = computed(() => {
  return !!recurringCostComponent.value
})

// Format unit type
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

// Payment schedule for pay-to-own
const paymentSchedule = computed(() => {
  if (!isPayToOwn.value || !recurringCostComponent.value || !formData.value.costStructure?.item_total_cost) {
    return null
  }

  const totalCost = formData.value.costStructure.item_total_cost
  const initialPay = formData.value.initialPayment || 0
  const remainingBalance = totalCost - initialPay
  const recurringRate = recurringCostComponent.value.rate

  if (remainingBalance <= 0 || recurringRate <= 0) {
    return null
  }

  const numberOfPayments = Math.ceil(remainingBalance / recurringRate)

  let timeUnit = ''
  let totalTime = numberOfPayments

  switch (recurringCostComponent.value.unit_type) {
    case 'per_month':
      timeUnit = numberOfPayments === 1 ? 'month' : 'months'
      break
    case 'per_week':
      timeUnit = numberOfPayments === 1 ? 'week' : 'weeks'
      break
    case 'per_year':
      timeUnit = numberOfPayments === 1 ? 'year' : 'years'
      break
    case 'per_day':
      timeUnit = numberOfPayments === 1 ? 'day' : 'days'
      break
    default:
      timeUnit = 'periods'
  }

  return {
    totalCost,
    initialPayment: initialPay,
    remainingBalance,
    recurringRate,
    numberOfPayments,
    totalTime,
    timeUnit,
    unitType: recurringCostComponent.value.unit_type
  }
})

// Available durations
const availableDurations = computed(() => {
  if (!formData.value.costStructure || !formData.value.costStructure.duration_options) {
    return []
  }

  const durationOptions = formData.value.costStructure.duration_options

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

// Update due date
const updateDueDate = () => {
  calculateCostEstimate()
}

// Calculate cost estimate
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

// Form validation
const isFormValid = computed(() => {
  const baseValid = formData.value.hub_id &&
                    formData.value.user &&
                    formData.value.costStructure &&
                    formData.value.pue_id

  if (isPayToOwn.value) {
    return baseValid
  }

  return baseValid && formData.value.duration
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

// Handle submit
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
      pue_id: formData.value.pue_id,
      cost_structure_id: formData.value.costStructure.cost_structure_id || formData.value.costStructure.structure_id,
      rental_start_date: formData.value.rentalStartDate ? new Date(formData.value.rentalStartDate).toISOString() : undefined,
      is_pay_to_own: isPayToOwn.value,
      pay_to_own_price: isPayToOwn.value ? formData.value.costStructure.item_total_cost : undefined,
      initial_payment: isPayToOwn.value && formData.value.initialPayment > 0 ? formData.value.initialPayment : undefined,
      has_recurring_payment: isPayToOwn.value || formData.value.enableRecurring,
      notes: formData.value.notes ? [formData.value.notes] : undefined
    }

    const response = await pueRentalsAPI.create(rentalData)

    $q.notify({
      type: 'positive',
      message: isPayToOwn.value ? 'Pay-to-own rental created successfully!' : 'PUE rental created successfully!',
      position: 'top'
    })

    emit('success', response.data)
  } catch (error) {
    console.error('Failed to create PUE rental:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create PUE rental',
      position: 'top'
    })
    emit('error', error)
  } finally {
    submitting.value = false
  }
}
</script>
