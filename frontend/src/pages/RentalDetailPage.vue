<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <q-btn flat round dense icon="arrow_back" @click="$router.back()" />
        <span class="text-h4 q-ml-md">Rental #{{ $route.params.id }}</span>
      </div>
      <div class="col-auto">
        <q-btn
          v-if="rental && rental.rental?.status === 'active'"
          label="Return Rental"
          icon="assignment_return"
          color="positive"
          @click="showReturnDialog = true"
        />
      </div>
    </div>

    <div v-if="loading" class="flex flex-center q-pa-xl">
      <q-spinner-gears size="50px" color="primary" />
    </div>

    <div v-else-if="rental" class="row q-col-gutter-md">
      <div class="col-12">
        <q-banner v-if="rental.rental?.status === 'overdue'" class="bg-negative text-white">
          <template v-slot:avatar>
            <q-icon name="warning" />
          </template>
          This rental is overdue!
        </q-banner>
      </div>

      <!-- Rental Info -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Rental Information</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <div><strong>ID:</strong> {{ rental.rental?.id || rental.rental?.rentral_id }}</div>
            <div>
              <strong>User:</strong>
              <q-btn
                flat
                dense
                color="primary"
                :label="rental.user?.Name || rental.user?.username || `User ${rental.rental?.user_id}`"
                icon="person"
                :to="{ name: 'user-detail', params: { id: rental.rental?.user_id } }"
                class="q-ml-sm"
              />
            </div>
            <div>
              <strong>Battery:</strong>
              <q-btn
                flat
                dense
                color="primary"
                :label="rental.battery?.short_id || `Battery ${rental.rental?.battery_id}`"
                icon="battery_charging_full"
                :to="{ name: 'battery-detail', params: { id: rental.rental?.battery_id } }"
                class="q-ml-sm"
              />
              <q-badge
                v-if="rental.summary?.battery_returned"
                color="grey"
                class="q-ml-sm"
              >
                Returned
              </q-badge>
              <q-btn
                v-else-if="rental.rental?.status === 'active' || rental.rental?.status === 'overdue'"
                flat
                dense
                size="sm"
                label="Return Battery"
                icon="assignment_return"
                color="positive"
                @click="showReturnDialog = true"
                class="q-ml-sm"
              />
            </div>
            <div>
              <strong>Status:</strong>
              <q-badge :color="getStatusColor(rental.rental?.status)" class="q-ml-sm" text-color="white">
                {{ rental.rental?.status }}
              </q-badge>
            </div>
            <div><strong>Rental Date:</strong> {{ formatDate(rental.rental?.rental_date) }}</div>
            <div><strong>Expected Return:</strong> {{ formatDate(rental.rental?.expected_return_date) }}</div>
            <div v-if="rental.rental?.actual_return_date">
              <strong>Actual Return:</strong> {{ formatDate(rental.rental?.actual_return_date) }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Costs -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Cost Breakdown</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <div><strong>Daily Rate:</strong> ${{ rental.rental?.daily_rate }}</div>
            <div><strong>Deposit:</strong> ${{ rental.rental?.deposit_amount }}</div>
            <div><strong>Days Rented:</strong> {{ calculateDays(rental.rental) }}</div>
            <div class="text-h6 text-primary q-mt-md">
              <strong>Total Cost:</strong> ${{ rental.rental?.total_cost?.toFixed(2) || '0.00' }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- PUE Items -->
      <div class="col-12" v-if="rental.pue_items && rental.pue_items.length > 0">
        <q-card>
          <q-card-section>
            <div class="text-h6">Equipment (PUE) Items</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list separator>
              <q-item v-for="item in rental.pue_items" :key="item.id">
                <q-item-section avatar>
                  <q-icon name="devices" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ item.pue?.name || `PUE #${item.pue_id}` }}</q-item-label>
                  <q-item-label caption>
                    Rented: {{ formatDate(item.added_at || item.rental_date) }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="row items-center q-gutter-sm">
                    <q-badge v-if="item.returned_date" color="grey">
                      Returned: {{ formatDate(item.returned_date) }}
                    </q-badge>
                    <q-badge v-else color="positive">Active</q-badge>
                    <q-btn
                      v-if="!item.returned_date"
                      flat
                      dense
                      round
                      size="sm"
                      icon="assignment_return"
                      color="positive"
                      @click="returnPUEItem(item)"
                    >
                      <q-tooltip>Return this item</q-tooltip>
                    </q-btn>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <!-- Notes -->
      <div class="col-12" v-if="rental.rental?.return_notes">
        <q-card>
          <q-card-section>
            <div class="text-h6">Return Notes</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            {{ rental.rental?.return_notes }}
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Unified Rental Return Dialog -->
    <RentalReturnDialog
      v-model="showReturnDialog"
      :rental="rental?.rental"
      @returned="onRentalReturned"
    />

    <!-- Return PUE Item Dialog -->
    <q-dialog v-model="showPUEReturnDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Return PUE Item</div>
          <div class="text-subtitle2">{{ selectedPUEItem?.pue?.name || `PUE #${selectedPUEItem?.pue_id}` }}</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input
            v-model="pueReturnNotes"
            type="textarea"
            label="Return Notes"
            hint="Optional notes about the item condition"
            rows="3"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Confirm Return" color="positive" @click="confirmPUEReturn" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { rentalsAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'
import RentalReturnDialog from 'components/RentalReturnDialog.vue'

const $q = useQuasar()
const route = useRoute()
const router = useRouter()

const rental = ref(null)
const loading = ref(true)
const showReturnDialog = ref(false)
const returnNotes = ref('')
const showBatteryReturnDialog = ref(false)
const showPUEReturnDialog = ref(false)
const selectedPUEItem = ref(null)
const batteryCondition = ref('good')
const pueReturnNotes = ref('')

// Full return dialog state
const fullReturnCondition = ref('good')
const fullReturnNotes = ref('')
const returnDeposit = ref(true)
const returnPaymentAmount = ref(0)
const returnPaymentType = ref(null)
const confirmReturnPayment = ref(false)
const paymentTypeOptions = ['Cash', 'Mobile Money', 'Bank Transfer', 'Credit Card']
const needsPayment = ref(false)
const kwhEndReading = ref(null)
const calculatedCost = ref(null)
const calculatingCost = ref(false)

const getStatusColor = (status) => {
  const colors = {
    active: 'positive',
    returned: 'grey',
    overdue: 'negative',
    cancelled: 'warning'
  }
  return colors[status] || 'grey'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm')
}

const calculateDays = (rental) => {
  if (!rental.rental_date || !rental.expected_return_date) return 0

  const start = new Date(rental.rental_date)
  const end = rental.actual_return_date
    ? new Date(rental.actual_return_date)
    : new Date(rental.expected_return_date)

  return Math.ceil((end - start) / (1000 * 60 * 60 * 24))
}

const loadRentalDetails = async () => {
  loading.value = true

  try {
    const rentalId = route.params.id
    const response = await rentalsAPI.get(rentalId)
    rental.value = response.data
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load rental details',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const confirmBatteryReturn = async () => {
  try {
    await rentalsAPI.return(route.params.id, {
      return_battery: true,
      return_pue_items: [],  // Don't return PUE items
      battery_condition: batteryCondition.value,
      return_notes: returnNotes.value || ''
    })

    $q.notify({
      type: 'positive',
      message: 'Battery returned successfully',
      position: 'top'
    })

    showBatteryReturnDialog.value = false
    returnNotes.value = ''
    batteryCondition.value = 'good'
    // Reload rental details to show updated status
    await loadRentalDetails()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return battery',
      position: 'top'
    })
  }
}

const returnPUEItem = (item) => {
  selectedPUEItem.value = item
  pueReturnNotes.value = ''
  showPUEReturnDialog.value = true
}

const confirmPUEReturn = async () => {
  try {
    await rentalsAPI.return(route.params.id, {
      return_battery: false,
      return_pue_items: [selectedPUEItem.value.id],
      return_notes: pueReturnNotes.value || ''
    })

    $q.notify({
      type: 'positive',
      message: 'PUE item returned successfully',
      position: 'top'
    })

    showPUEReturnDialog.value = false
    pueReturnNotes.value = ''
    selectedPUEItem.value = null
    // Reload rental details to show updated status
    await loadRentalDetails()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return PUE item',
      position: 'top'
    })
  }
}

const calculateReturnCost = async () => {
  calculatingCost.value = true
  try {
    const params = {}
    if (kwhEndReading.value) {
      params.kwh_usage = kwhEndReading.value
    }

    const response = await rentalsAPI.calculateReturnCost(route.params.id, params)
    calculatedCost.value = response.data

    // Update the needsPayment flag
    if (calculatedCost.value.payment_status?.amount_still_owed > 0) {
      needsPayment.value = true
    }

    $q.notify({
      type: 'positive',
      message: 'Cost calculated successfully',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to calculate cost',
      position: 'top'
    })
  } finally {
    calculatingCost.value = false
  }
}

const confirmFullReturn = async () => {
  try {
    const returnData = {
      battery_return_condition: fullReturnCondition.value,
      battery_return_notes: fullReturnNotes.value,
      return_deposit: returnDeposit.value
    }

    // Add kWh reading if provided
    if (kwhEndReading.value) {
      returnData.kwh_end_reading = kwhEndReading.value
    }

    // If cost was recalculated, update the rental total
    if (calculatedCost.value) {
      returnData.final_cost = calculatedCost.value.total
    }

    // If payment is being collected, add payment info
    if (returnPaymentAmount.value > 0 && returnPaymentType.value) {
      returnData.payment_amount = returnPaymentAmount.value
      returnData.payment_type = returnPaymentType.value
    }

    await rentalsAPI.returnBattery(route.params.id, returnData)

    $q.notify({
      type: 'positive',
      message: 'Rental returned successfully',
      position: 'top'
    })

    showReturnDialog.value = false
    fullReturnCondition.value = 'good'
    fullReturnNotes.value = ''
    returnDeposit.value = true
    returnPaymentAmount.value = 0
    returnPaymentType.value = null
    confirmReturnPayment.value = false
    kwhEndReading.value = null
    calculatedCost.value = null

    // Reload rental details to show updated status
    await loadRentalDetails()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to return rental',
      position: 'top'
    })
  }
}

const onRentalReturned = async () => {
  // Reload rental details after successful return
  await loadRentalDetails()
}

onMounted(() => {
  loadRentalDetails()
})
</script>
