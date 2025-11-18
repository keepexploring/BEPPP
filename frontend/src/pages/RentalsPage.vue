<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h4">Rentals</div>
      </div>
      <div class="col-auto q-gutter-sm">
        <q-btn
          label="New Rental"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <!-- Filter tabs -->
    <q-tabs
      v-model="statusFilter"
      dense
      class="text-grey"
      active-color="primary"
      indicator-color="primary"
      align="justify"
      narrow-indicator
      @update:model-value="loadRentals"
    >
      <q-tab name="all" label="All Rentals" />
      <q-tab name="active" label="Active" />
      <q-tab name="returned" label="Returned" />
      <q-tab name="overdue" label="Overdue" />
    </q-tabs>

    <q-card class="q-mt-md">
      <q-card-section>
        <q-table
          :rows="rentals"
          :columns="columns"
          row-key="id"
          :loading="loading"
          :filter="filter"
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

          <template v-slot:body-cell-rental_date="props">
            <q-td :props="props">
              {{ formatDate(props.row.rental_date) }}
            </q-td>
          </template>

          <template v-slot:body-cell-expected_return_date="props">
            <q-td :props="props">
              {{ formatDate(props.row.expected_return_date) }}
            </q-td>
          </template>

          <template v-slot:body-cell-total_cost="props">
            <q-td :props="props">
              ${{ props.row.total_cost?.toFixed(2) || '0.00' }}
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                dense
                icon="visibility"
                color="primary"
                :to="{ name: 'rental-detail', params: { id: props.row.id } }"
              />
              <q-btn
                v-if="props.row.status === 'active'"
                flat
                round
                dense
                icon="assignment_return"
                color="positive"
                @click="returnRental(props.row)"
              >
                <q-tooltip>Return Rental</q-tooltip>
              </q-btn>
              <q-btn
                v-if="authStore.isAdmin"
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click="editRental(props.row)"
              />
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Create/Edit Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">{{ editingRental ? 'Edit Rental' : 'New Rental' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveRental" class="q-gutter-md">
            <q-select
              v-model="formData.hub_id"
              :options="hubOptions"
              option-value="id"
              option-label="name"
              emit-value
              map-options
              label="Hub"
              outlined
              :rules="[val => !!val || 'Hub is required']"
              @update:model-value="onHubChange"
            />

            <q-select
              v-model="formData.user_id"
              :options="userOptions"
              option-value="id"
              option-label="username"
              emit-value
              map-options
              label="User"
              outlined
              :rules="[val => !!val || 'User is required']"
            />

            <q-select
              v-model="formData.battery_id"
              :options="availableBatteries"
              option-value="id"
              option-label="serial_number"
              emit-value
              map-options
              label="Battery"
              outlined
              :rules="[val => !!val || 'Battery is required']"
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.serial_number }}</q-item-label>
                    <q-item-label caption>{{ scope.opt.capacity }}Wh - {{ scope.opt.model }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input
                  v-model="formData.rental_date"
                  label="Rental Date"
                  type="datetime-local"
                  outlined
                  :rules="[val => !!val || 'Rental date is required']"
                />
              </div>
              <div class="col-6">
                <q-input
                  v-model="formData.expected_return_date"
                  label="Expected Return Date"
                  type="datetime-local"
                  outlined
                  :rules="[val => !!val || 'Expected return date is required']"
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input
                  v-model.number="formData.daily_rate"
                  label="Daily Rate"
                  type="number"
                  step="0.01"
                  outlined
                  prefix="$"
                  :rules="[val => val >= 0 || 'Rate must be positive']"
                />
              </div>
              <div class="col-6">
                <q-input
                  v-model.number="formData.deposit_amount"
                  label="Deposit Amount"
                  type="number"
                  step="0.01"
                  outlined
                  prefix="$"
                />
              </div>
            </div>

            <q-separator />

            <div class="text-subtitle2">Add PUE Items (Optional)</div>
            <q-select
              :options="availablePUE"
              option-value="id"
              option-label="name"
              label="Select Equipment to Add"
              outlined
              @update:model-value="addPUEToRental"
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.name }}</q-item-label>
                    <q-item-label caption>${{ scope.opt.daily_rate }}/day - {{ scope.opt.description }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <q-list v-if="formData.pue_items && formData.pue_items.length > 0" bordered separator>
              <q-item v-for="(item, index) in formData.pue_items" :key="index">
                <q-item-section>
                  <q-item-label>{{ getPUEName(item.pue_id) }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="close"
                    color="negative"
                    @click="removePUEItem(index)"
                  />
                </q-item-section>
              </q-item>
            </q-list>

            <div class="row justify-end q-gutter-sm">
              <q-btn label="Cancel" flat @click="closeDialog" />
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

    <!-- Return Rental Dialog -->
    <q-dialog v-model="showReturnDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Return Rental</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="confirmReturn" class="q-gutter-md">
            <q-input
              v-model="returnData.actual_return_date"
              label="Return Date"
              type="datetime-local"
              outlined
              :rules="[val => !!val || 'Return date is required']"
            />

            <q-input
              v-model="returnData.return_notes"
              label="Return Notes"
              type="textarea"
              outlined
              rows="3"
              hint="Note the condition of the battery and any issues"
            />

            <div class="row justify-end q-gutter-sm">
              <q-btn label="Cancel" flat v-close-popup />
              <q-btn
                label="Confirm Return"
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
import { ref, onMounted } from 'vue'
import { rentalsAPI, hubsAPI, usersAPI, batteriesAPI, pueAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar, date } from 'quasar'

const $q = useQuasar()
const authStore = useAuthStore()

const rentals = ref([])
const hubOptions = ref([])
const userOptions = ref([])
const availableBatteries = ref([])
const availablePUE = ref([])
const loading = ref(false)
const filter = ref('')
const statusFilter = ref('all')
const showCreateDialog = ref(false)
const showReturnDialog = ref(false)
const editingRental = ref(null)
const returningRental = ref(null)
const saving = ref(false)

const formData = ref({
  hub_id: null,
  user_id: null,
  battery_id: null,
  rental_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
  expected_return_date: date.formatDate(
    date.addToDate(new Date(), { days: 7 }),
    'YYYY-MM-DDTHH:mm'
  ),
  daily_rate: 5.0,
  deposit_amount: 50.0,
  pue_items: []
})

const returnData = ref({
  actual_return_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
  return_notes: ''
})

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true },
  { name: 'user', label: 'User', field: row => row.user?.username || row.user_id, align: 'left', sortable: true },
  { name: 'battery', label: 'Battery', field: row => row.battery?.serial_number || row.battery_id, align: 'left' },
  { name: 'rental_date', label: 'Rental Date', field: 'rental_date', align: 'left', sortable: true },
  { name: 'expected_return_date', label: 'Expected Return', field: 'expected_return_date', align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
  { name: 'total_cost', label: 'Total Cost', field: 'total_cost', align: 'left', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center' }
]

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

const loadRentals = async () => {
  loading.value = true
  try {
    // Since there's no list all rentals endpoint, we need to get rentals from users
    // For now, we'll show a placeholder or load from hubs
    rentals.value = []

    $q.notify({
      type: 'info',
      message: 'Rental listing needs user selection',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load rentals',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

const onHubChange = async (hubId) => {
  if (!hubId) return

  try {
    // Load available batteries for this hub
    const batteriesResponse = await hubsAPI.getBatteries(hubId)
    availableBatteries.value = batteriesResponse.data.filter(
      b => b.status === 'available'
    )

    // Load available PUE for this hub
    const pueResponse = await hubsAPI.getAvailablePUE(hubId)
    availablePUE.value = pueResponse.data

    // Load users for this hub
    const usersResponse = await hubsAPI.getUsers(hubId)
    userOptions.value = usersResponse.data
  } catch (error) {
    console.error('Failed to load hub data:', error)
  }
}

const addPUEToRental = (pue) => {
  if (!pue) return

  if (!formData.value.pue_items.find(item => item.pue_id === pue.id)) {
    formData.value.pue_items.push({
      pue_id: pue.id
    })
  }
}

const removePUEItem = (index) => {
  formData.value.pue_items.splice(index, 1)
}

const getPUEName = (pueId) => {
  const pue = availablePUE.value.find(p => p.id === pueId)
  return pue?.name || pueId
}

const editRental = (rental) => {
  editingRental.value = rental
  formData.value = {
    ...rental,
    rental_date: date.formatDate(rental.rental_date, 'YYYY-MM-DDTHH:mm'),
    expected_return_date: date.formatDate(rental.expected_return_date, 'YYYY-MM-DDTHH:mm')
  }
  showCreateDialog.value = true
}

const saveRental = async () => {
  saving.value = true
  try {
    const rentalData = {
      ...formData.value,
      rental_date: new Date(formData.value.rental_date).toISOString(),
      expected_return_date: new Date(formData.value.expected_return_date).toISOString()
    }

    if (editingRental.value) {
      await rentalsAPI.update(editingRental.value.id, rentalData)
      $q.notify({
        type: 'positive',
        message: 'Rental updated successfully',
        position: 'top'
      })
    } else {
      await rentalsAPI.create(rentalData)
      $q.notify({
        type: 'positive',
        message: 'Rental created successfully',
        position: 'top'
      })
    }

    closeDialog()
    loadRentals()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to save rental',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const returnRental = (rental) => {
  returningRental.value = rental
  returnData.value = {
    actual_return_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
    return_notes: ''
  }
  showReturnDialog.value = true
}

const confirmReturn = async () => {
  saving.value = true
  try {
    await rentalsAPI.returnBattery(returningRental.value.id, {
      actual_return_date: new Date(returnData.value.actual_return_date).toISOString(),
      return_notes: returnData.value.return_notes
    })

    $q.notify({
      type: 'positive',
      message: 'Rental returned successfully',
      position: 'top'
    })

    showReturnDialog.value = false
    loadRentals()
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

const closeDialog = () => {
  showCreateDialog.value = false
  resetForm()
}

const resetForm = () => {
  formData.value = {
    hub_id: null,
    user_id: null,
    battery_id: null,
    rental_date: date.formatDate(new Date(), 'YYYY-MM-DDTHH:mm'),
    expected_return_date: date.formatDate(
      date.addToDate(new Date(), { days: 7 }),
      'YYYY-MM-DDTHH:mm'
    ),
    daily_rate: 5.0,
    deposit_amount: 50.0,
    pue_items: []
  }
  editingRental.value = null
}

onMounted(() => {
  loadRentals()
  loadHubs()
})
</script>
