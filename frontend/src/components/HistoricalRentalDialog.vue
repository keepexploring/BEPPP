<template>
  <q-dialog v-model="show" persistent maximized>
    <q-card style="display: flex; flex-direction: column; height: 100%">
      <q-card-section class="row items-center q-py-sm">
        <q-icon name="history" size="sm" class="q-mr-sm text-primary" />
        <div class="text-h6">Add Historical Rental Records</div>
        <q-badge v-if="savedRecords.length" color="positive" class="q-ml-sm">
          {{ savedRecords.length }} saved
        </q-badge>
        <q-space />
        <q-btn icon="close" flat round dense @click="close" />
      </q-card-section>

      <q-separator />

      <!-- Saved records table (shown after first save) -->
      <div v-if="savedRecords.length" class="q-px-md q-pt-sm" style="max-height: 220px; overflow-y: auto">
        <div class="text-caption text-grey-6 q-mb-xs">Records added this session</div>
        <q-table
          :rows="savedRecords"
          :columns="savedColumns"
          dense
          flat
          bordered
          hide-bottom
          :rows-per-page-options="[0]"
          class="text-caption"
        >
          <template v-slot:body-cell-customer="props">
            <q-td :props="props">{{ props.row.customerName }}</q-td>
          </template>
          <template v-slot:body-cell-dates="props">
            <q-td :props="props">{{ props.row.startLabel }} → {{ props.row.returnLabel }}</q-td>
          </template>
          <template v-slot:body-cell-paid="props">
            <q-td :props="props">
              <span v-if="props.row.amount_paid">{{ currencySymbol }}{{ props.row.amount_paid }}</span>
              <span v-else class="text-grey-5">—</span>
            </q-td>
          </template>
        </q-table>
      </div>

      <q-separator v-if="savedRecords.length" class="q-mt-sm" />

      <!-- Entry form -->
      <q-card-section class="q-gutter-sm col" style="overflow-y: auto">
        <div class="text-caption text-grey-7">
          Enter past rental records from paper. Availability check is skipped — battery is marked returned immediately.
        </div>

        <div class="row q-col-gutter-sm">
          <!-- Left column -->
          <div class="col-12 col-md-6 q-gutter-sm">

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
              dense
              clearable
              :rules="[val => !!val || 'Required']"
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
                <q-item><q-item-section class="text-grey">Type to search</q-item-section></q-item>
              </template>
            </q-select>

            <!-- Battery ID -->
            <q-input
              v-model="form.battery_id"
              label="Battery ID *"
              outlined
              dense
              clearable
              autofocus
              :rules="[val => !!val || 'Required']"
              @keyup.enter="focusNext('startDate')"
            >
              <template v-slot:prepend><q-icon name="battery_charging_full" /></template>
            </q-input>

            <!-- Cost structure -->
            <q-select
              v-model="form.cost_structure_id"
              :options="costStructureOptions"
              option-label="name"
              option-value="structure_id"
              label="Cost Structure (optional)"
              outlined
              dense
              clearable
              emit-value
              map-options
            >
              <template v-slot:prepend><q-icon name="receipt" /></template>
            </q-select>

          </div>

          <!-- Right column -->
          <div class="col-12 col-md-6 q-gutter-sm">

            <!-- Start date -->
            <q-input
              ref="startDateRef"
              v-model="form.rental_start_date"
              label="Rental Start *"
              type="datetime-local"
              outlined
              dense
              :rules="[val => !!val || 'Required']"
            />

            <!-- Return date -->
            <q-input
              v-model="form.actual_return_date"
              label="Return Date *"
              type="datetime-local"
              outlined
              dense
              :rules="[val => !!val || 'Required']"
            />

            <!-- Payment row -->
            <div class="row q-col-gutter-sm">
              <div class="col-7">
                <q-input
                  v-model.number="form.amount_paid"
                  label="Amount Paid"
                  type="number"
                  min="0"
                  outlined
                  dense
                  :prefix="currencySymbol"
                >
                  <template v-slot:prepend><q-icon name="payments" /></template>
                </q-input>
              </div>
              <div class="col-5">
                <q-select
                  v-model="form.payment_type"
                  :options="paymentTypeOptions"
                  option-label="label"
                  option-value="value"
                  label="Method"
                  outlined
                  dense
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
              dense
              type="textarea"
              rows="2"
              autogrow
            />

          </div>
        </div>

        <!-- Keep customer checkbox -->
        <q-checkbox
          v-model="keepCustomer"
          label="Keep customer selected after saving"
          dense
          class="text-caption"
        />
      </q-card-section>

      <q-separator />

      <q-card-actions align="right" class="q-pa-sm">
        <q-btn flat label="Close" @click="close" />
        <q-btn
          label="Save & Add Another"
          color="secondary"
          icon="add"
          outline
          :loading="submitting"
          @click="submit(true)"
        />
        <q-btn
          label="Save & Close"
          color="primary"
          icon="save"
          :loading="submitting"
          @click="submit(false)"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar, date } from 'quasar'
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
const keepCustomer = ref(true)
const savedRecords = ref([])
const startDateRef = ref(null)

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

const savedColumns = [
  { name: 'customer', label: 'Customer', field: 'customerName', align: 'left' },
  { name: 'battery', label: 'Battery', field: 'battery_id', align: 'left' },
  { name: 'dates', label: 'Dates', field: 'dates', align: 'left' },
  { name: 'paid', label: 'Paid', field: 'amount_paid', align: 'right' }
]

const focusNext = (ref) => {
  if (ref === 'startDate') startDateRef.value?.$el?.querySelector('input')?.focus()
}

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

const submit = async (addAnother) => {
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

    savedRecords.value.unshift({
      customerName: form.value.selectedUser.displayName,
      battery_id: form.value.battery_id.trim(),
      amount_paid: form.value.amount_paid || null,
      startLabel: date.formatDate(form.value.rental_start_date, 'DD MMM YY'),
      returnLabel: date.formatDate(form.value.actual_return_date, 'DD MMM YY')
    })

    emit('saved')

    if (addAnother) {
      const prevUser = keepCustomer.value ? form.value.selectedUser : null
      resetForm()
      form.value.selectedUser = prevUser
      $q.notify({ type: 'positive', message: 'Saved — ready for next record', position: 'top', timeout: 1500 })
    } else {
      show.value = false
      resetForm()
      $q.notify({ type: 'positive', message: `${savedRecords.value.length} historical record${savedRecords.value.length > 1 ? 's' : ''} saved`, position: 'top' })
    }
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

const close = () => {
  const count = savedRecords.value.length
  show.value = false
  savedRecords.value = []
  resetForm()
  if (count > 0) {
    $q.notify({ type: 'positive', message: `Session closed — ${count} record${count > 1 ? 's' : ''} saved`, position: 'top' })
  }
}

onMounted(loadCostStructures)
</script>
