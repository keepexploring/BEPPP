<template>
  <q-dialog v-model="show" persistent>
    <q-card style="min-width: 400px; max-width: 600px; width: 90vw">
      <q-card-section class="row items-center">
        <div class="text-h6">Add Historical Rental Record</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-separator />

      <q-card-section class="q-gutter-md">
        <div class="text-caption text-grey-7">
          Enter past rental records from paper. The battery availability check is skipped.
        </div>

        <!-- Customer search -->
        <q-select
          v-model="form.selectedUser"
          :options="userOptions"
          option-label="displayName"
          option-value="user_id"
          use-input
          input-debounce="300"
          label="Customer *"
          outlined
          clearable
          :rules="[val => !!val || 'Customer is required']"
          @filter="searchUsers"
        >
          <template v-slot:prepend><q-icon name="person" /></template>
          <template v-slot:option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section>
                <q-item-label>{{ scope.opt.displayName }}</q-item-label>
                <q-item-label caption>{{ scope.opt.mobile_number }}</q-item-label>
              </q-item-section>
            </q-item>
          </template>
          <template v-slot:no-option>
            <q-item><q-item-section class="text-grey">Type to search customers</q-item-section></q-item>
          </template>
        </q-select>

        <!-- Battery ID -->
        <q-input
          v-model="form.battery_id"
          label="Battery ID *"
          outlined
          :rules="[val => !!val || 'Battery ID is required']"
        >
          <template v-slot:prepend><q-icon name="battery_charging_full" /></template>
        </q-input>

        <!-- Rental dates -->
        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-6">
            <q-input
              v-model="form.rental_start_date"
              label="Rental Start Date *"
              type="datetime-local"
              outlined
              :rules="[val => !!val || 'Start date is required']"
            />
          </div>
          <div class="col-12 col-sm-6">
            <q-input
              v-model="form.actual_return_date"
              label="Return Date *"
              type="datetime-local"
              outlined
              :rules="[val => !!val || 'Return date is required']"
            />
          </div>
        </div>

        <!-- Cost structure (optional) -->
        <q-select
          v-model="form.cost_structure_id"
          :options="costStructureOptions"
          option-label="name"
          option-value="structure_id"
          label="Cost Structure (optional)"
          outlined
          clearable
          emit-value
          map-options
        >
          <template v-slot:prepend><q-icon name="receipt" /></template>
        </q-select>

        <!-- Payment -->
        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-6">
            <q-input
              v-model.number="form.amount_paid"
              label="Amount Paid"
              type="number"
              min="0"
              outlined
              :prefix="currencySymbol"
            >
              <template v-slot:prepend><q-icon name="payments" /></template>
            </q-input>
          </div>
          <div class="col-12 col-sm-6">
            <q-select
              v-model="form.payment_type"
              :options="paymentTypeOptions"
              option-label="label"
              option-value="value"
              label="Payment Method"
              outlined
              emit-value
              map-options
            />
          </div>
        </div>

        <!-- Notes -->
        <q-input
          v-model="form.notes"
          label="Notes (optional)"
          outlined
          type="textarea"
          rows="2"
          autogrow
        />
      </q-card-section>

      <q-card-actions align="right" class="q-pa-md">
        <q-btn flat label="Cancel" v-close-popup />
        <q-btn
          label="Save Record"
          color="primary"
          icon="save"
          :loading="submitting"
          @click="submit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import api, { settingsAPI } from 'src/services/api.js'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useAuthStore } from 'stores/auth'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'saved'])

const $q = useQuasar()
const hubSettingsStore = useHubSettingsStore()
const authStore = useAuthStore()

const show = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

const submitting = ref(false)
const userOptions = ref([])
const costStructureOptions = ref([])

const form = ref({
  selectedUser: null,
  battery_id: '',
  rental_start_date: '',
  actual_return_date: '',
  cost_structure_id: null,
  amount_paid: null,
  payment_type: 'cash',
  notes: ''
})

const paymentTypeOptions = [
  { label: 'Cash', value: 'cash' },
  { label: 'Mobile Money', value: 'mobile_money' },
  { label: 'Bank Transfer', value: 'bank_transfer' },
  { label: 'Card', value: 'card' }
]

const searchUsers = async (val, update) => {
  if (!val || val.length < 2) {
    update(() => { userOptions.value = [] })
    return
  }
  try {
    const hubId = authStore.user?.hub_id
    const params = { search: val, limit: 20 }
    if (hubId) params.hub_id = hubId
    const response = await api.get('/users', { params })
    update(() => {
      userOptions.value = (response.data || []).map(u => ({
        ...u,
        displayName: `${u.first_names || ''} ${u.last_name || u.Name || ''}`.trim() || u.username
      }))
    })
  } catch {
    update(() => { userOptions.value = [] })
  }
}

const loadCostStructures = async () => {
  try {
    const hubId = authStore.user?.hub_id
    const response = await settingsAPI.getCostStructures({ hub_id: hubId, is_active: true })
    costStructureOptions.value = response.data || []
  } catch {
    costStructureOptions.value = []
  }
}

const submit = async () => {
  if (!form.value.selectedUser || !form.value.battery_id || !form.value.rental_start_date || !form.value.actual_return_date) {
    $q.notify({ type: 'warning', message: 'Please fill in all required fields', position: 'top' })
    return
  }

  submitting.value = true
  try {
    const payload = {
      user_id: form.value.selectedUser.user_id,
      battery_ids: [form.value.battery_id.trim()],
      rental_start_date: new Date(form.value.rental_start_date).toISOString(),
      actual_return_date: new Date(form.value.actual_return_date).toISOString(),
      cost_structure_id: form.value.cost_structure_id || null,
      amount_paid: form.value.amount_paid || null,
      payment_type: form.value.amount_paid ? form.value.payment_type : null,
      notes: form.value.notes ? [form.value.notes] : null
    }

    await api.post('/battery-rentals', payload)

    $q.notify({ type: 'positive', message: 'Historical rental record saved', position: 'top' })
    emit('saved')
    show.value = false
    resetForm()
  } catch (err) {
    $q.notify({ type: 'negative', message: err.response?.data?.detail || 'Failed to save record', position: 'top' })
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    selectedUser: null,
    battery_id: '',
    rental_start_date: '',
    actual_return_date: '',
    cost_structure_id: null,
    amount_paid: null,
    payment_type: 'cash',
    notes: ''
  }
}

onMounted(loadCostStructures)
</script>
