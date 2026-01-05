<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" @click="$router.back()" class="q-mr-md" />
      <div class="text-h4 col">Create Battery Rental</div>
    </div>

    <q-card>
      <q-card-section>
        <div class="text-h6 q-mb-md">Rental Information</div>

        <div class="row q-col-gutter-md">
          <!-- User Selection -->
          <div class="col-12 col-md-6">
            <q-select
              v-model="selectedUser"
              :options="userOptions"
              option-value="user_id"
              option-label="Name"
              label="Select User *"
              outlined
              use-input
              input-debounce="300"
              @filter="filterUsers"
              :loading="usersLoading"
              :rules="[val => !!val || 'User is required']"
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

          <!-- Cost Structure Selection -->
          <div class="col-12 col-md-6">
            <q-select
              v-model="selectedCostStructure"
              :options="costStructureOptions"
              option-value="cost_structure_id"
              option-label="name"
              label="Cost Structure *"
              outlined
              :loading="costStructuresLoading"
              :rules="[val => !!val || 'Cost structure is required']"
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

          <!-- Battery Selection -->
          <div class="col-12">
            <div class="text-subtitle2 q-mb-sm">Select Batteries *</div>
            <q-input
              v-model="batterySearchFilter"
              outlined
              dense
              placeholder="Search batteries..."
              class="q-mb-sm"
            >
              <template v-slot:prepend>
                <q-icon name="search" />
              </template>
            </q-input>

            <div v-if="batteriesLoading" class="row justify-center q-pa-md">
              <q-spinner color="primary" size="2em" />
            </div>

            <div v-else-if="availableBatteries.length === 0" class="text-grey-7 q-pa-md text-center">
              <q-icon name="battery_unknown" size="48px" class="q-mb-sm" />
              <div>No available batteries found</div>
            </div>

            <div v-else class="q-gutter-sm">
              <q-chip
                v-for="battery in filteredBatteries"
                :key="battery.battery_id"
                :selected="selectedBatteries.includes(battery.battery_id)"
                clickable
                color="primary"
                text-color="white"
                @click="toggleBattery(battery.battery_id)"
              >
                <q-avatar :icon="selectedBatteries.includes(battery.battery_id) ? 'check_circle' : 'circle'" />
                Battery #{{ battery.battery_id }}
                <span v-if="battery.model" class="q-ml-xs">({{ battery.model }})</span>
              </q-chip>
            </div>
            <div v-if="selectedBatteries.length > 0" class="text-caption text-positive q-mt-sm">
              {{ selectedBatteries.length }} battery(ies) selected
            </div>
            <div v-else class="text-caption text-negative q-mt-sm">
              Please select at least one battery
            </div>
          </div>

          <!-- Rental Start Date -->
          <div class="col-12 col-md-6">
            <q-input
              v-model="rentalStartDate"
              label="Rental Start Date"
              outlined
              type="datetime-local"
            >
              <template v-slot:prepend>
                <q-icon name="event" />
              </template>
            </q-input>
          </div>

          <!-- Due Date -->
          <div class="col-12 col-md-6">
            <q-input
              v-model="dueDate"
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
              v-model.number="depositAmount"
              label="Deposit Amount (Optional)"
              outlined
              type="number"
              step="0.01"
              min="0"
            >
              <template v-slot:prepend>
                <q-icon name="account_balance_wallet" />
              </template>
            </q-input>
          </div>

          <!-- Notes -->
          <div class="col-12">
            <q-input
              v-model="notes"
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

      <q-card-section>
        <div class="row justify-end q-gutter-sm">
          <q-btn
            flat
            label="Cancel"
            color="grey"
            @click="$router.back()"
          />
          <q-btn
            label="Create Rental"
            color="primary"
            icon="add"
            @click="createRental"
            :loading="submitting"
            :disable="!isFormValid"
          />
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { usersAPI, batteriesAPI, settingsAPI, batteryRentalsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const authStore = useAuthStore()

// Form data
const selectedUser = ref(null)
const selectedCostStructure = ref(null)
const selectedBatteries = ref([])
const rentalStartDate = ref(new Date().toISOString().slice(0, 16)) // datetime-local format
const dueDate = ref(null)
const depositAmount = ref(0)
const notes = ref('')

// Data loading
const usersLoading = ref(false)
const batteriesLoading = ref(false)
const costStructuresLoading = ref(false)
const submitting = ref(false)

// Options
const userOptions = ref([])
const allUsers = ref([])
const availableBatteries = ref([])
const costStructureOptions = ref([])

// Battery search filter
const batterySearchFilter = ref('')

const filteredBatteries = computed(() => {
  if (!batterySearchFilter.value) return availableBatteries.value

  const search = batterySearchFilter.value.toLowerCase()
  return availableBatteries.value.filter(b =>
    b.battery_id.toString().includes(search) ||
    b.model?.toLowerCase().includes(search)
  )
})

const isFormValid = computed(() => {
  return selectedUser.value &&
    selectedCostStructure.value &&
    selectedBatteries.value.length > 0
})

// Load users
const loadUsers = async () => {
  try {
    usersLoading.value = true
    const hubId = authStore.currentHubId

    if (hubId) {
      const response = await usersAPI.get(hubId)
      allUsers.value = response.data?.users || []
      userOptions.value = allUsers.value
    }
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

const filterUsers = (val, update) => {
  update(() => {
    if (val === '') {
      userOptions.value = allUsers.value
    } else {
      const needle = val.toLowerCase()
      userOptions.value = allUsers.value.filter(u =>
        u.Name?.toLowerCase().includes(needle) ||
        u.username?.toLowerCase().includes(needle) ||
        u.mobile_number?.includes(needle) ||
        u.user_id?.toString().includes(needle)
      )
    }
  })
}

// Load available batteries
const loadBatteries = async () => {
  try {
    batteriesLoading.value = true
    const hubId = authStore.currentHubId

    const response = await batteriesAPI.list({ hub_id: hubId, status: 'available' })
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

// Load cost structures
const loadCostStructures = async () => {
  try {
    costStructuresLoading.value = true
    const hubId = authStore.currentHubId

    const response = await settingsAPI.getCostStructures({ hub_id: hubId })
    costStructureOptions.value = response.data || []
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

// Toggle battery selection
const toggleBattery = (batteryId) => {
  const index = selectedBatteries.value.indexOf(batteryId)
  if (index === -1) {
    selectedBatteries.value.push(batteryId)
  } else {
    selectedBatteries.value.splice(index, 1)
  }
}

// Create rental
const createRental = async () => {
  if (!isFormValid.value) {
    $q.notify({
      type: 'warning',
      message: 'Please fill in all required fields',
      position: 'top'
    })
    return
  }

  try {
    submitting.value = true

    const rentalData = {
      user_id: selectedUser.value.user_id,
      battery_ids: selectedBatteries.value,
      cost_structure_id: selectedCostStructure.value.cost_structure_id,
      rental_start_date: rentalStartDate.value ? new Date(rentalStartDate.value).toISOString() : undefined,
      due_date: dueDate.value ? new Date(dueDate.value).toISOString() : undefined,
      deposit_amount: depositAmount.value > 0 ? depositAmount.value : undefined,
      notes: notes.value ? [notes.value] : undefined
    }

    await batteryRentalsAPI.create(rentalData)

    $q.notify({
      type: 'positive',
      message: 'Battery rental created successfully',
      position: 'top'
    })

    // Navigate back to user detail page
    router.push(`/users/${selectedUser.value.user_id}`)
  } catch (error) {
    console.error('Failed to create rental:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to create rental',
      position: 'top'
    })
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  // Load data
  await Promise.all([
    loadUsers(),
    loadBatteries(),
    loadCostStructures()
  ])

  // Pre-select user if user_id is in query params
  if (route.query.user_id) {
    const userId = parseInt(route.query.user_id)
    const user = allUsers.value.find(u => u.user_id === userId)
    if (user) {
      selectedUser.value = user
    }
  }
})
</script>

<style scoped>
.q-chip {
  cursor: pointer;
}
</style>
