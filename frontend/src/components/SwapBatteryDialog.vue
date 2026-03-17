<template>
  <q-dialog v-model="showDialog" @hide="onHide">
    <q-card style="min-width: 500px; max-width: 700px">
      <q-card-section>
        <div class="text-h6">Swap Battery</div>
        <div class="text-caption" v-if="rental">
          Rental #{{ rental.rental_id }}
        </div>
      </q-card-section>

      <!-- Rental Info Card -->
      <q-card-section v-if="rental" class="q-pt-none">
        <q-card flat bordered class="bg-grey-1">
          <q-card-section class="q-pa-sm">
            <div class="row q-col-gutter-sm">
              <div class="col-6">
                <div class="text-caption text-grey-7">Current Battery</div>
                <div class="text-body2 text-weight-medium">#{{ currentBatteryId }}</div>
              </div>
              <div class="col-6">
                <div class="text-caption text-grey-7">Remaining Days</div>
                <div class="text-body2 text-weight-medium">{{ remainingDaysDisplay }}</div>
              </div>
              <div class="col-6">
                <div class="text-caption text-grey-7">Swaps Used</div>
                <div class="text-body2 text-weight-medium">
                  {{ rental.recharges_used || 0 }}{{ rental.max_recharges ? ' / ' + rental.max_recharges : '' }}
                </div>
              </div>
              <div class="col-6" v-if="rechargeFee > 0">
                <div class="text-caption text-grey-7">Recharge Fee</div>
                <div class="text-body2 text-weight-medium">{{ rechargeFee.toFixed(2) }} {{ currencySymbol }}</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </q-card-section>

      <!-- Swap Limit Reached Banner -->
      <q-card-section v-if="swapLimitReached" class="q-pt-none">
        <q-banner class="bg-negative text-white" rounded>
          <template v-slot:avatar>
            <q-icon name="block" />
          </template>
          Maximum swaps ({{ rental.max_recharges }}) reached for this rental.
        </q-banner>
      </q-card-section>

      <!-- Battery Selection -->
      <q-card-section v-if="!swapLimitReached" class="q-pt-none">
        <div class="text-subtitle2 q-mb-sm">Select New Battery *</div>
        <q-input
          v-model="batterySearch"
          outlined dense
          placeholder="Search batteries..."
          class="q-mb-sm"
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>

        <div v-if="loadingBatteries" class="row justify-center q-pa-md">
          <q-spinner color="primary" size="2em" />
        </div>

        <div v-else-if="filteredBatteries.length === 0" class="text-grey-7 q-pa-md text-center">
          <q-icon name="battery_unknown" size="48px" class="q-mb-sm" />
          <div>No available batteries found</div>
        </div>

        <div v-else class="q-gutter-sm" style="max-height: 200px; overflow-y: auto">
          <q-chip
            v-for="battery in filteredBatteries"
            :key="battery.battery_id"
            :selected="selectedBatteryId === battery.battery_id"
            clickable
            color="primary"
            text-color="white"
            @click="selectedBatteryId = battery.battery_id"
          >
            <q-avatar :icon="selectedBatteryId === battery.battery_id ? 'radio_button_checked' : 'radio_button_unchecked'" />
            Battery #{{ battery.battery_id }}
            <span v-if="battery.short_id" class="q-ml-xs">({{ battery.short_id }})</span>
          </q-chip>
        </div>
        <div v-if="selectedBatteryId" class="text-caption text-positive q-mt-sm">
          Battery #{{ selectedBatteryId }} selected
        </div>
      </q-card-section>

      <!-- Payment Section -->
      <q-card-section v-if="rechargeFee > 0 && !swapLimitReached && selectedBatteryId" class="q-pt-none">
        <q-separator class="q-mb-md" />
        <div class="text-subtitle2 q-mb-sm">Payment</div>

        <div class="row q-col-gutter-sm">
          <div class="col-6">
            <q-select
              v-model="paymentType"
              :options="paymentTypeOptions"
              label="Payment Type"
              outlined dense
              emit-value
              map-options
            />
          </div>
          <div class="col-6">
            <q-input
              v-model.number="paymentAmount"
              type="number"
              label="Payment Amount"
              outlined dense
              :prefix="currencySymbol"
            />
          </div>
        </div>

        <q-checkbox
          v-model="paymentConfirmed"
          label="Confirm payment taken"
          class="q-mt-sm"
        />
      </q-card-section>

      <!-- Actions -->
      <q-card-actions align="right">
        <q-btn flat label="Cancel" color="grey" @click="showDialog = false" />
        <q-btn
          label="Complete Swap"
          color="primary"
          :loading="saving"
          :disable="!canComplete"
          @click="completeSwap"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { batteryRentalsAPI, batteriesAPI } from 'src/services/api'
import { useHubSettingsStore } from 'stores/hubSettings'

const $q = useQuasar()
const hubSettingsStore = useHubSettingsStore()
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

const emit = defineEmits(['update:modelValue', 'swapped'])

const showDialog = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const selectedBatteryId = ref(null)
const batterySearch = ref('')
const availableBatteries = ref([])
const loadingBatteries = ref(false)
const saving = ref(false)
const paymentType = ref('cash')
const paymentAmount = ref(0)
const paymentConfirmed = ref(false)

const paymentTypeOptions = [
  { label: 'Cash', value: 'cash' },
  { label: 'Mobile Money', value: 'mobile_money' },
  { label: 'Bank Transfer', value: 'bank_transfer' },
  { label: 'Card', value: 'card' }
]

const currentBatteryId = computed(() => {
  if (!props.rental) return null
  return props.rental.battery_id || (props.rental.batteries?.find(b => !b.returned_at)?.battery_id) || null
})

const rechargeFee = computed(() => {
  if (!props.rental?.cost_structure?.components) return 0
  const rechargeComp = props.rental.cost_structure.components.find(
    c => c.component_name === 'per_recharge'
  )
  return rechargeComp ? parseFloat(rechargeComp.rate) : 0
})

const swapLimitReached = computed(() => {
  if (!props.rental) return false
  return props.rental.max_recharges != null && (props.rental.recharges_used || 0) >= props.rental.max_recharges
})

const remainingDaysDisplay = computed(() => {
  if (!props.rental?.rental_end_date) return 'N/A'
  const end = new Date(props.rental.rental_end_date)
  const now = new Date()
  const diff = (end - now) / (1000 * 60 * 60 * 24)
  if (diff <= 0) return 'Overdue'
  return diff.toFixed(1) + ' days'
})

const filteredBatteries = computed(() => {
  if (!batterySearch.value) return availableBatteries.value
  const search = batterySearch.value.toLowerCase()
  return availableBatteries.value.filter(b =>
    b.battery_id.toLowerCase().includes(search) ||
    (b.short_id && b.short_id.toLowerCase().includes(search))
  )
})

const canComplete = computed(() => {
  if (!selectedBatteryId.value) return false
  if (swapLimitReached.value) return false
  if (rechargeFee.value > 0 && !paymentConfirmed.value) return false
  return true
})

const loadAvailableBatteries = async () => {
  if (!props.rental) return
  loadingBatteries.value = true
  try {
    const response = await batteriesAPI.list({
      hub_id: props.rental.hub_id,
      status: 'available'
    })
    availableBatteries.value = Array.isArray(response.data) ? response.data : (response.data.batteries || [])
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to load batteries', position: 'top' })
  } finally {
    loadingBatteries.value = false
  }
}

const completeSwap = async () => {
  if (!canComplete.value) return
  saving.value = true
  try {
    const payload = {
      new_battery_id: selectedBatteryId.value,
      payment_type: paymentType.value
    }
    if (rechargeFee.value > 0) {
      payload.payment_amount = paymentAmount.value || 0
    }
    await batteryRentalsAPI.swapBattery(props.rental.rental_id, payload)
    $q.notify({ type: 'positive', message: 'Battery swapped successfully', position: 'top' })
    emit('swapped')
    showDialog.value = false
  } catch (error) {
    const msg = error.response?.data?.detail || 'Failed to swap battery'
    $q.notify({ type: 'negative', message: msg, position: 'top' })
  } finally {
    saving.value = false
  }
}

const onHide = () => {
  selectedBatteryId.value = null
  batterySearch.value = ''
  paymentAmount.value = 0
  paymentConfirmed.value = false
}

watch(() => props.modelValue, (val) => {
  if (val && props.rental) {
    loadAvailableBatteries()
    paymentAmount.value = rechargeFee.value
  }
})
</script>
