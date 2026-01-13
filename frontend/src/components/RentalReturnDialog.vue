<template>
  <q-dialog v-model="showDialog" @hide="onHide">
    <q-card style="min-width: 700px; max-width: 900px">
      <q-card-section>
        <div class="text-h6">Return Rental</div>
        <div class="text-caption" v-if="rental">
          Rental ID: {{ rental.rental_unique_id || rental.rentral_id }}
        </div>
      </q-card-section>

      <!-- Loading State -->
      <q-card-section v-if="loadingCost && !costCalculation" class="q-pt-none">
        <q-card flat bordered>
          <q-card-section class="text-center q-py-md">
            <q-spinner color="primary" size="40px" />
            <div class="text-caption q-mt-sm">Calculating final cost based on usage...</div>
          </q-card-section>
        </q-card>
      </q-card-section>

      <!-- Cost Breakdown Section -->
      <q-card-section v-if="costCalculation" class="q-pt-none">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2 q-mb-md">Final Cost Calculation</div>

            <div>
              <!-- Duration Info -->
              <div class="row q-col-gutter-sm q-mb-md">
                <div class="col-6">
                  <div class="text-caption text-grey-7">Rental Duration</div>
                  <div class="text-body2">{{ costCalculation.duration.actual_days.toFixed(1) }} days ({{ costCalculation.duration.actual_hours.toFixed(1) }} hours)</div>
                </div>
                <div class="col-6" v-if="costCalculation.duration.is_late">
                  <q-badge color="negative" class="q-pa-sm">
                    <q-icon name="warning" class="q-mr-xs" />
                    Late Return
                  </q-badge>
                </div>
              </div>

              <!-- kWh Usage (if applicable) -->
              <div v-if="costCalculation.kwh_usage.total_used !== null" class="row q-mb-md">
                <div class="col-12">
                  <div class="text-caption text-grey-7">kWh Usage</div>
                  <div class="text-body2">{{ costCalculation.kwh_usage.total_used.toFixed(2) }} kWh</div>
                </div>
              </div>

              <!-- Subscription Coverage (if applicable) -->
              <div v-if="costCalculation.subscription" class="q-mb-md">
                <q-banner
                  :class="costCalculation.subscription.is_covered ? 'bg-positive text-white' : 'bg-info text-white'"
                  rounded
                >
                  <template v-slot:avatar>
                    <q-icon :name="costCalculation.subscription.is_covered ? 'verified' : 'info'" />
                  </template>
                  <div class="text-weight-bold">
                    {{ costCalculation.subscription.is_covered ? 'Subscription Coverage Active' : 'Subscription Info' }}
                  </div>
                  <div class="text-body2">{{ costCalculation.subscription.subscription_name }}</div>

                  <div v-if="costCalculation.subscription.is_covered" class="q-mt-sm">
                    <div class="row q-gutter-sm text-caption">
                      <div class="col-12">
                        <div>Covered Amount: {{ currencySymbol }}{{ costCalculation.subscription.covered_amount.toFixed(2) }}</div>
                        <div v-if="costCalculation.subscription.kwh_overage > 0" class="q-mt-xs">
                          <q-icon name="warning" size="xs" class="q-mr-xs" />
                          kWh Overage: {{ costCalculation.subscription.kwh_overage.toFixed(2) }} kWh
                          (Extra: {{ currencySymbol }}{{ costCalculation.subscription.kwh_overage_cost.toFixed(2) }})
                        </div>
                        <div class="q-mt-xs">
                          kWh Used This Period: {{ costCalculation.subscription.kwh_used_this_period.toFixed(1) }} / {{ costCalculation.subscription.kwh_included }} kWh
                        </div>
                        <div v-if="costCalculation.subscription.remaining_cost_after_subscription > 0" class="q-mt-xs text-weight-bold">
                          You Still Owe: {{ currencySymbol }}{{ costCalculation.subscription.remaining_cost_after_subscription.toFixed(2) }}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-caption q-mt-xs">
                    {{ costCalculation.subscription.message }}
                  </div>
                </q-banner>
              </div>

              <!-- Cost Breakdown Table -->
              <q-markup-table flat dense class="q-mb-md">
                <thead>
                  <tr>
                    <th class="text-left">Component</th>
                    <th class="text-right">Rate</th>
                    <th class="text-right">Quantity</th>
                    <th class="text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="component in costCalculation.cost_breakdown" :key="component.component_name">
                    <td>{{ component.component_name }}</td>
                    <td class="text-right">{{ currencySymbol }}{{ component.rate.toFixed(2) }} / {{ component.unit_type.replace('per_', '') }}</td>
                    <td class="text-right">{{ component.quantity }}</td>
                    <td class="text-right">{{ currencySymbol }}{{ component.amount.toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td colspan="3" class="text-right text-weight-medium">Subtotal:</td>
                    <td class="text-right text-weight-medium">{{ currencySymbol }}{{ costCalculation.subtotal.toFixed(2) }}</td>
                  </tr>
                  <tr v-if="costCalculation.vat_amount > 0">
                    <td colspan="3" class="text-right">VAT ({{ costCalculation.vat_percentage }}%):</td>
                    <td class="text-right">{{ currencySymbol }}{{ costCalculation.vat_amount.toFixed(2) }}</td>
                  </tr>
                  <tr>
                    <td colspan="3" class="text-right text-weight-bold text-h6">Total:</td>
                    <td class="text-right text-weight-bold text-h6">{{ currencySymbol }}{{ costCalculation.total.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </q-markup-table>

              <!-- Payment Status -->
              <div class="q-gutter-sm">
                <div class="row">
                  <div class="col">Original Estimate:</div>
                  <div class="col text-right">{{ currencySymbol }}{{ costCalculation.original_estimate.toFixed(2) }}</div>
                </div>
                <div class="row">
                  <div class="col">Amount Paid So Far:</div>
                  <div class="col text-right text-positive">-{{ currencySymbol }}{{ costCalculation.payment_status.amount_paid_so_far.toFixed(2) }}</div>
                </div>
                <q-separator class="q-my-sm" />
                <div class="row text-weight-bold">
                  <div class="col">Amount Still Owed:</div>
                  <div class="col text-right" :class="costCalculation.payment_status.amount_still_owed > 0 ? 'text-negative' : 'text-positive'">
                    {{ currencySymbol }}{{ costCalculation.payment_status.amount_still_owed.toFixed(2) }}
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </q-card-section>

      <!-- Return Form -->
      <q-card-section>
        <q-form @submit="onConfirm" class="q-gutter-md">
          <!-- kWh End Reading -->
          <q-input
            v-model.number="formData.kwhEndReading"
            type="number"
            label="Battery kWh End Reading (optional)"
            hint="Enter current kWh reading for accurate cost calculation"
            outlined
            step="0.01"
            @update:model-value="recalculateCost"
          >
            <template v-slot:prepend>
              <q-icon name="power" />
            </template>
            <template v-slot:append>
              <q-btn
                flat
                dense
                round
                icon="refresh"
                @click="recalculateCost"
                :loading="loadingCost"
              >
                <q-tooltip>Recalculate with current reading</q-tooltip>
              </q-btn>
            </template>
          </q-input>

          <!-- Return Date -->
          <q-input
            v-model="formData.actual_return_date"
            label="Return Date"
            outlined
            type="datetime-local"
          >
            <template v-slot:prepend>
              <q-icon name="event" />
            </template>
          </q-input>

          <!-- Return Notes -->
          <q-input
            v-model="formData.return_notes"
            label="Return Notes"
            type="textarea"
            outlined
            rows="3"
          >
            <template v-slot:prepend>
              <q-icon name="note" />
            </template>
          </q-input>

          <!-- Payment Collection -->
          <div v-if="costCalculation">
            <q-separator class="q-my-md" />
            <div class="text-subtitle2 q-mb-md">Payment Collection</div>

            <!-- Subscription Coverage Info (if applicable) -->
            <q-banner v-if="costCalculation.subscription && costCalculation.subscription.is_covered"
              class="bg-positive text-white q-mb-md" rounded dense>
              <template v-slot:avatar>
                <q-icon name="verified" />
              </template>
              <div class="text-weight-bold">Subscription: {{ costCalculation.subscription.subscription_name }}</div>
              <div class="text-caption">
                Covered by subscription: {{ currencySymbol }}{{ costCalculation.subscription.covered_amount.toFixed(2) }}
                <span v-if="costCalculation.subscription.remaining_cost_after_subscription > 0">
                  | Additional charges: {{ currencySymbol }}{{ costCalculation.subscription.remaining_cost_after_subscription.toFixed(2) }}
                </span>
              </div>
            </q-banner>

            <!-- Amount Summary -->
            <q-card flat bordered class="q-mb-md">
              <q-card-section>
                <div class="row q-gutter-sm">
                  <div class="col">
                    <div class="text-caption text-grey-7">
                      {{ costCalculation.subscription && costCalculation.subscription.is_covered ? 'Additional Amount Owed' : 'Total Amount Owed' }}
                    </div>
                    <div class="text-h6 text-negative">{{ currencySymbol }}{{ costCalculation.payment_status.amount_still_owed.toFixed(2) }}</div>
                    <div v-if="costCalculation.subscription && costCalculation.subscription.is_covered" class="text-caption text-grey-7">
                      (After {{ currencySymbol }}{{ costCalculation.subscription.covered_amount.toFixed(2) }} subscription coverage)
                    </div>
                  </div>
                  <div v-if="costCalculation.payment_status.user_account_balance > 0" class="col">
                    <div class="text-caption text-grey-7">User's Available Credit</div>
                    <div class="text-h6 text-positive">{{ currencySymbol }}{{ costCalculation.payment_status.user_account_balance.toFixed(2) }}</div>
                  </div>
                </div>
              </q-card-section>
            </q-card>

            <q-checkbox
              v-model="formData.collectPayment"
              label="Collect payment now"
              class="q-mb-md"
            />

            <div v-if="formData.collectPayment" class="q-gutter-md">
              <!-- Apply Credit Amount (always show, disabled if no credit) -->
              <div>
                <q-input
                  v-model.number="formData.credit_applied"
                  type="number"
                  label="Credit to Apply"
                  outlined
                  step="0.01"
                  :prefix="currencySymbol"
                  :disable="costCalculation.payment_status.user_account_balance <= 0"
                  :max="Math.min(costCalculation.payment_status.user_account_balance, costCalculation.payment_status.amount_still_owed)"
                  :hint="costCalculation.payment_status.user_account_balance > 0
                    ? `Max available: ${currencySymbol}${Math.min(costCalculation.payment_status.user_account_balance, costCalculation.payment_status.amount_still_owed).toFixed(2)}`
                    : 'User has no account credit'"
                  @update:model-value="onCreditAmountChange"
                >
                  <template v-slot:prepend>
                    <q-icon name="account_balance_wallet" :color="costCalculation.payment_status.user_account_balance > 0 ? 'positive' : 'grey'" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      flat
                      dense
                      color="positive"
                      label="Use Max"
                      size="sm"
                      @click="onUseMaxCredit"
                      :disable="costCalculation.payment_status.user_account_balance <= 0"
                    />
                  </template>
                </q-input>
              </div>

              <!-- Cash Payment Amount -->
              <q-input
                v-model.number="formData.payment_amount"
                type="number"
                label="Cash Payment Amount"
                outlined
                step="0.01"
                :prefix="currencySymbol"
                @update:model-value="onCashAmountChange"
              >
                <template v-slot:prepend>
                  <q-icon name="payments" color="primary" />
                </template>
                <template v-slot:hint>
                  <div class="row items-center q-gutter-xs">
                    <span>After applying credit: {{ currencySymbol }}{{ remainingAfterCredit.toFixed(2) }}</span>
                  </div>
                </template>
              </q-input>

              <!-- Remaining Balance (Debt) -->
              <div v-if="remainingDebt > 0" class="q-pa-md bg-orange-1 rounded-borders">
                <div class="row items-center">
                  <q-icon name="warning" color="orange" size="sm" class="q-mr-sm" />
                  <div>
                    <div class="text-caption text-grey-7">Remaining Balance (will be added to user's debt)</div>
                    <div class="text-weight-bold text-orange">{{ currencySymbol }}{{ remainingDebt.toFixed(2) }}</div>
                  </div>
                </div>
              </div>

              <!-- Overpayment (Credit) -->
              <div v-if="remainingDebt < 0" class="q-pa-md bg-green-1 rounded-borders">
                <div class="row items-center">
                  <q-icon name="add_circle" color="positive" size="sm" class="q-mr-sm" />
                  <div>
                    <div class="text-caption text-grey-7">Overpayment (will be added to user's credit)</div>
                    <div class="text-weight-bold text-positive">{{ currencySymbol }}{{ Math.abs(remainingDebt).toFixed(2) }}</div>
                  </div>
                </div>
              </div>

              <!-- Payment Summary -->
              <q-card flat bordered class="bg-grey-1">
                <q-card-section>
                  <div class="text-caption text-weight-bold q-mb-sm">Payment Summary</div>

                  <!-- Original Total (if subscription exists) -->
                  <div v-if="costCalculation.subscription && costCalculation.subscription.is_covered" class="row q-mb-xs text-grey-7">
                    <div class="col">Original Total:</div>
                    <div class="col text-right">{{ currencySymbol }}{{ costCalculation.total.toFixed(2) }}</div>
                  </div>
                  <div v-if="costCalculation.subscription && costCalculation.subscription.is_covered" class="row q-mb-xs text-positive">
                    <div class="col">- Subscription Coverage:</div>
                    <div class="col text-right">-{{ currencySymbol }}{{ costCalculation.subscription.covered_amount.toFixed(2) }}</div>
                  </div>

                  <!-- Current Amount Owed -->
                  <div class="row q-mb-xs" :class="costCalculation.subscription && costCalculation.subscription.is_covered ? '' : 'text-weight-medium'">
                    <div class="col">{{ costCalculation.subscription && costCalculation.subscription.is_covered ? 'Additional Amount Owed:' : 'Amount Owed:' }}</div>
                    <div class="col text-right">{{ currencySymbol }}{{ costCalculation.payment_status.amount_still_owed.toFixed(2) }}</div>
                  </div>

                  <!-- Credit Applied -->
                  <div v-if="formData.credit_applied > 0" class="row q-mb-xs text-positive">
                    <div class="col">- User Credit Applied:</div>
                    <div class="col text-right">-{{ currencySymbol }}{{ formData.credit_applied.toFixed(2) }}</div>
                  </div>

                  <!-- Cash Payment -->
                  <div v-if="formData.payment_amount > 0" class="row q-mb-xs text-primary">
                    <div class="col">- Cash Payment:</div>
                    <div class="col text-right">-{{ currencySymbol }}{{ formData.payment_amount.toFixed(2) }}</div>
                  </div>

                  <q-separator class="q-my-sm" />

                  <!-- Remaining Balance -->
                  <div class="row text-weight-bold">
                    <div class="col">
                      <span v-if="remainingDebt > 0">Remaining Balance:</span>
                      <span v-else-if="remainingDebt < 0">Overpayment:</span>
                      <span v-else>Remaining Balance:</span>
                    </div>
                    <div class="col text-right" :class="remainingDebt > 0 ? 'text-orange' : remainingDebt < 0 ? 'text-positive' : 'text-positive'">
                      {{ currencySymbol }}{{ Math.abs(remainingDebt).toFixed(2) }}
                    </div>
                  </div>

                  <!-- Balance Assignment Info -->
                  <div v-if="remainingDebt !== 0" class="q-mt-sm q-pa-sm rounded-borders" :class="remainingDebt > 0 ? 'bg-orange-2' : 'bg-green-2'">
                    <div class="text-caption text-weight-medium">
                      <q-icon name="info" size="xs" class="q-mr-xs" />
                      <span v-if="remainingDebt > 0">
                        <span v-if="costCalculation.subscription && costCalculation.subscription.is_covered">
                          Will be charged to subscription's monthly billing
                        </span>
                        <span v-else>
                          Will be added to user's account as debt
                        </span>
                      </span>
                      <span v-else>
                        Will be added to user's account as credit
                      </span>
                    </div>
                  </div>
                </q-card-section>
              </q-card>

              <!-- Payment Type -->
              <q-select
                v-model="formData.payment_type"
                :options="paymentTypeOptions"
                label="Payment Type (for cash payment)"
                outlined
                emit-value
                map-options
              />

              <!-- Payment Notes -->
              <q-input
                v-model="formData.payment_notes"
                label="Payment Notes (optional)"
                type="textarea"
                outlined
                rows="2"
              />

              <!-- Payment Confirmation -->
              <q-separator class="q-my-md" />
              <!-- Show confirmation checkbox only when actual payment is being collected -->
              <div v-if="formData.payment_amount > 0 && formData.payment_type" class="bg-positive-1 q-pa-md rounded-borders">
                <div class="text-weight-medium q-mb-sm">
                  <q-icon name="check_circle" color="positive" class="q-mr-sm" />
                  Payment Confirmation
                </div>
                <q-checkbox
                  v-model="confirmPaymentReceived"
                  color="positive"
                >
                  <template v-slot:default>
                    <div class="text-body2">
                      I confirm that <strong>{{ formData.payment_type }}</strong> payment of
                      <strong>{{ currencySymbol }}{{ (formData.payment_amount || 0).toFixed(2) }}</strong> has been received<span v-if="formData.credit_applied > 0">, and <strong>{{ currencySymbol }}{{ formData.credit_applied.toFixed(2) }}</strong> will be taken from the user's account credit</span>
                    </div>
                  </template>
                </q-checkbox>
              </div>
              <!-- When only credit is used, show informational message -->
              <div v-else-if="formData.credit_applied > 0 && formData.payment_amount === 0 && formData.payment_type" class="bg-positive-1 q-pa-md rounded-borders">
                <div class="text-weight-medium q-mb-sm">
                  <q-icon name="account_balance_wallet" color="positive" class="q-mr-sm" />
                  Credit Payment
                </div>
                <div class="text-body2">
                  <strong>{{ currencySymbol }}{{ formData.credit_applied.toFixed(2) }}</strong> will be taken from the user's account credit to cover this payment.
                </div>
              </div>

              <!-- Make Payment Button -->
              <div class="q-mt-md">
                <q-btn
                  :label="formData.payment_amount > 0 ? 'Record Payment' : 'Apply Credit Payment'"
                  color="positive"
                  icon="payment"
                  :disable="((formData.payment_amount || 0) + (formData.credit_applied || 0)) <= 0 || !formData.payment_type || (formData.payment_amount > 0 && !confirmPaymentReceived)"
                  @click="recordPayment"
                  class="full-width"
                />
              </div>

              <!-- Payment Success Message -->
              <div v-if="paymentReceived" class="q-mt-md bg-positive text-white q-pa-md rounded-borders">
                <q-icon name="check_circle" size="sm" class="q-mr-sm" />
                Payment recorded successfully! You can now confirm the return.
              </div>
            </div>
          </div>

          <!-- Actions -->
          <q-separator class="q-mt-lg" />
          <div class="row justify-end q-gutter-sm q-mt-md">
            <q-btn label="Cancel" flat @click="onCancel" />
            <q-btn
              label="Confirm Return"
              color="primary"
              :loading="saving"
              :disable="formData.collectPayment && !paymentReceived"
              @click="onConfirm"
            />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useQuasar, date } from 'quasar'
import { batteryRentalsAPI, pueRentalsAPI, settingsAPI } from 'src/services/api'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useAuthStore } from 'stores/auth'

const $q = useQuasar()
const hubSettingsStore = useHubSettingsStore()
const authStore = useAuthStore()

const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  rental: {
    type: Object,
    default: null
  }
})

// Computed to determine rental type and select appropriate API
const rentalType = computed(() => {
  if (!props.rental) return 'battery' // default to battery
  // Check if it's a PUE rental
  if (props.rental.rental_type === 'pue' || props.rental.pue_rental_id || props.rental.pue_id) {
    return 'pue'
  }
  return 'battery'
})

const rentalAPI = computed(() => {
  return rentalType.value === 'pue' ? pueRentalsAPI : batteryRentalsAPI
})

const emit = defineEmits(['update:modelValue', 'returned'])

const showDialog = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const costCalculation = ref(null)
const loadingCost = ref(false)
const saving = ref(false)
const paymentReceived = ref(false)
const confirmPaymentReceived = ref(false)
const paymentTypeOptions = ref([])

const formData = ref({
  kwhEndReading: null,
  actual_return_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
  return_notes: '',
  collectPayment: false,
  payment_type: null,
  payment_amount: 0,
  credit_applied: 0,
  payment_notes: '',
  useAccountCredit: false
})

// Watch for dialog opening
watch(() => props.rental, async (newRental) => {
  console.log('Rental prop changed:', newRental)
  if (newRental) {
    // Reset form
    formData.value = {
      kwhEndReading: newRental.kwh_usage_end || null,
      actual_return_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
      return_notes: '',
      collectPayment: false,
      payment_type: 'cash',
      payment_amount: 0,
      credit_applied: 0,
      payment_notes: '',
      useAccountCredit: false
    }
    paymentReceived.value = false
    confirmPaymentReceived.value = false

    console.log('Fetching cost calculation for rental...')
    // Fetch cost calculation
    await fetchCostCalculation()
  }
}, { immediate: true })

// Watch collectPayment checkbox - reset payment received when unchecked
watch(() => formData.value.collectPayment, (newValue) => {
  if (!newValue) {
    paymentReceived.value = false
    confirmPaymentReceived.value = false
  }
})

const fetchCostCalculation = async () => {
  if (!props.rental) {
    console.warn('No rental prop provided to fetchCostCalculation')
    return
  }

  // Extract rental ID based on rental type
  const rentalId = props.rental.rental_id || props.rental.rentral_id || props.rental.pue_rental_id || props.rental.id
  if (!rentalId) {
    console.error('Rental object missing ID field. Checked: rental_id, rentral_id, pue_rental_id, id', props.rental)
    $q.notify({
      type: 'negative',
      message: 'Cannot calculate cost: rental ID is missing',
      position: 'top'
    })
    return
  }

  console.log('Fetching cost calculation for rental ID:', rentalId, 'Type:', rentalType.value)
  loadingCost.value = true
  try {
    const params = {}
    if (formData.value.kwhEndReading) {
      params.kwh_usage = formData.value.kwhEndReading
    }

    console.log('Calling API with params:', params)
    const response = await rentalAPI.value.calculateReturnCost(rentalId, params)
    console.log('Cost calculation response:', response.data)
    costCalculation.value = response.data

    // Update payment amount if owed
    if (costCalculation.value.payment_status.amount_still_owed > 0) {
      formData.value.collectPayment = true
      formData.value.payment_amount = costCalculation.value.payment_status.amount_still_owed
    }
  } catch (error) {
    console.error('Failed to fetch cost calculation:', error)
    console.error('Error details:', error.response?.data)
    console.error('Error status:', error.response?.status)
    const errorMsg = error.response?.data?.detail || error.message || 'Failed to calculate return cost'
    $q.notify({
      type: 'negative',
      message: `Cost Calculation Error: ${errorMsg}`,
      position: 'top',
      timeout: 5000
    })
  } finally {
    loadingCost.value = false
  }
}

const recalculateCost = async () => {
  await fetchCostCalculation()
}

// Computed properties for payment calculations
const remainingAfterCredit = computed(() => {
  if (!costCalculation.value) return 0
  const amountOwed = costCalculation.value.payment_status.amount_still_owed
  const creditApplied = formData.value.credit_applied || 0
  return Math.max(0, amountOwed - creditApplied)
})

const remainingDebt = computed(() => {
  if (!costCalculation.value) return 0
  const amountOwed = costCalculation.value.payment_status.amount_still_owed
  const creditApplied = formData.value.credit_applied || 0
  const cashPayment = formData.value.payment_amount || 0
  // Allow negative values to show overpayment
  return amountOwed - creditApplied - cashPayment
})

// Event handlers for credit and cash inputs
const onCreditAmountChange = (value) => {
  // Ensure credit doesn't exceed available or owed
  if (!costCalculation.value) return
  const maxCredit = Math.min(
    costCalculation.value.payment_status.user_account_balance,
    costCalculation.value.payment_status.amount_still_owed
  )
  if (value > maxCredit) {
    formData.value.credit_applied = maxCredit
  }

  // Auto-update cash payment to cover remaining amount
  const amountOwed = costCalculation.value.payment_status.amount_still_owed
  const creditApplied = formData.value.credit_applied || 0
  const remaining = Math.max(0, amountOwed - creditApplied)
  formData.value.payment_amount = remaining
}

const onUseMaxCredit = () => {
  if (!costCalculation.value) return
  const maxCredit = Math.min(
    costCalculation.value.payment_status.user_account_balance,
    costCalculation.value.payment_status.amount_still_owed
  )
  formData.value.credit_applied = maxCredit
  // Trigger the credit change handler
  onCreditAmountChange(maxCredit)
}

const onCashAmountChange = () => {
  // Allow any amount - overpayment will be added as credit to user's account
  // The remaining (if underpayment) will be tracked as debt
}

const recordPayment = () => {
  const totalPayment = (formData.value.payment_amount || 0) + (formData.value.credit_applied || 0)

  if (totalPayment <= 0) {
    $q.notify({
      type: 'warning',
      message: 'Total payment (cash + credit) must be greater than 0',
      position: 'top'
    })
    return
  }

  if (!formData.value.payment_type) {
    $q.notify({
      type: 'warning',
      message: 'Please select a payment method',
      position: 'top'
    })
    return
  }

  // Only require confirmation checkbox if actual cash/card payment is being collected
  if (formData.value.payment_amount > 0 && !confirmPaymentReceived.value) {
    $q.notify({
      type: 'warning',
      message: 'Please confirm that payment has been received',
      position: 'top'
    })
    return
  }

  // Mark payment as received
  paymentReceived.value = true

  $q.notify({
    type: 'positive',
    message: `Payment of ${currencySymbol.value}${totalPayment.toFixed(2)} confirmed. You can now complete the return.`,
    position: 'top'
  })
}

const onConfirm = async () => {
  saving.value = true
  try {
    const returnPayload = {
      actual_return_date: new Date(formData.value.actual_return_date).toISOString(),
      return_notes: formData.value.return_notes
    }

    // Add kWh reading if provided
    if (formData.value.kwhEndReading) {
      returnPayload.kwh_usage_end = formData.value.kwhEndReading
    }

    // Add payment info if collecting
    if (formData.value.collectPayment) {
      returnPayload.collect_payment = true
      returnPayload.payment_type = formData.value.payment_type
      returnPayload.payment_amount = formData.value.payment_amount || 0
      returnPayload.credit_applied = formData.value.credit_applied || 0
      returnPayload.payment_notes = formData.value.payment_notes
    }

    const returnMethod = rentalType.value === 'pue' ? 'returnPUE' : 'returnBattery'
    const rentalId = props.rental.rental_id || props.rental.rentral_id || props.rental.pue_rental_id || props.rental.id
    await rentalAPI.value[returnMethod](rentalId, returnPayload)

    $q.notify({
      type: 'positive',
      message: 'Rental returned successfully',
      position: 'top'
    })

    emit('returned')
    showDialog.value = false
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return rental',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const onCancel = () => {
  showDialog.value = false
}

const onHide = () => {
  costCalculation.value = null
}

const loadPaymentTypes = async () => {
  const hubId = authStore.user?.hub_id
  if (!hubId) return

  try {
    const response = await settingsAPI.getPaymentTypes({ hub_id: hubId, is_active: true })
    paymentTypeOptions.value = response.data.payment_types.map(pt => ({
      label: pt.type_name,
      value: pt.type_name
    }))

    // Set default payment type if available
    if (paymentTypeOptions.value.length > 0 && !formData.value.payment_type) {
      formData.value.payment_type = paymentTypeOptions.value[0].value
    }
  } catch (error) {
    console.error('Failed to load payment types:', error)
    // Fallback to default options
    paymentTypeOptions.value = [
      { label: 'Cash', value: 'cash' },
      { label: 'Mobile Money', value: 'mobile_money' },
      { label: 'Bank Transfer', value: 'bank_transfer' },
      { label: 'Card', value: 'card' }
    ]
    formData.value.payment_type = 'cash'
  }
}

onMounted(() => {
  loadPaymentTypes()
})
</script>
