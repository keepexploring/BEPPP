<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" @click="$router.back()" class="q-mr-md" />
      <div class="text-h4 col">Create PUE Rental</div>
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

          <!-- PUE Selection -->
          <div class="col-12">
            <q-select
              v-model="selectedPUE"
              :options="filteredPUEs"
              option-value="pue_id"
              label="Select PUE Item *"
              outlined
              use-input
              input-debounce="300"
              @filter="filterPUEs"
              :loading="puesLoading"
              :rules="[val => !!val || 'PUE item is required']"
            >
              <template v-slot:prepend>
                <q-icon name="devices_other" />
              </template>
              <template v-slot:selected>
                <span v-if="selectedPUE">
                  {{ selectedPUE.name || `PUE #${selectedPUE.pue_id}` }}
                  <span v-if="selectedPUE.pue_type_name" class="text-grey q-ml-xs">({{ selectedPUE.pue_type_name }})</span>
                </span>
              </template>
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.name || `PUE #${scope.opt.pue_id}` }}</q-item-label>
                    <q-item-label caption>
                      Type: {{ scope.opt.pue_type_name || 'N/A' }} | Status: {{ scope.opt.status }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
              <template v-slot:no-option>
                <q-item>
                  <q-item-section class="text-grey">
                    No available PUE items found
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
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

          <!-- Pay-to-Own Toggle -->
          <div class="col-12">
            <q-separator class="q-my-md" />
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle1">Pay-to-Own Option</div>
                <div class="text-caption text-grey">Enable if user is purchasing this item through payments</div>
              </div>
              <div class="col-auto">
                <q-toggle
                  v-model="isPayToOwn"
                  color="purple"
                  size="lg"
                  :label="isPayToOwn ? 'Enabled' : 'Disabled'"
                />
              </div>
            </div>
          </div>

          <!-- Pay-to-Own Fields (conditional) -->
          <template v-if="isPayToOwn">
            <div class="col-12">
              <q-banner class="bg-purple-1 text-purple-9 q-mb-md" rounded>
                <template v-slot:avatar>
                  <q-icon name="info" color="purple" />
                </template>
                <div class="text-subtitle2">Pay-to-Own Rental</div>
                <div class="text-caption">
                  The user will gradually own this item through payments. Once the total price is paid, ownership transfers to the user.
                </div>
              </q-banner>
            </div>

            <div class="col-12 col-md-6">
              <q-input
                v-model.number="payToOwnPrice"
                label="Total Price *"
                outlined
                type="number"
                step="0.01"
                min="0"
                :rules="[val => isPayToOwn ? (val > 0 || 'Price must be greater than 0') : true]"
              >
                <template v-slot:prepend>
                  <q-icon name="shopping_cart" />
                </template>
              </q-input>
            </div>

            <div class="col-12 col-md-6">
              <q-input
                v-model.number="initialPayment"
                label="Initial Payment (Optional)"
                outlined
                type="number"
                step="0.01"
                min="0"
                :max="payToOwnPrice"
              >
                <template v-slot:prepend>
                  <q-icon name="payment" />
                </template>
              </q-input>
            </div>

            <!-- Payment Progress Preview -->
            <div v-if="payToOwnPrice > 0" class="col-12">
              <q-card flat bordered class="bg-purple-1">
                <q-card-section>
                  <div class="text-subtitle2 text-purple-9 q-mb-sm">Payment Progress Preview</div>
                  <div class="row q-col-gutter-sm text-caption">
                    <div class="col-4">
                      <div class="text-grey-7">Total Price</div>
                      <div class="text-weight-bold">${{ payToOwnPrice.toFixed(2) }}</div>
                    </div>
                    <div class="col-4">
                      <div class="text-grey-7">Initial Payment</div>
                      <div class="text-weight-bold">${{ (initialPayment || 0).toFixed(2) }}</div>
                    </div>
                    <div class="col-4">
                      <div class="text-grey-7">Remaining</div>
                      <div class="text-weight-bold">${{ Math.max(0, payToOwnPrice - (initialPayment || 0)).toFixed(2) }}</div>
                    </div>
                  </div>
                  <q-linear-progress
                    :value="payToOwnPrice > 0 ? (initialPayment || 0) / payToOwnPrice : 0"
                    color="purple"
                    class="q-mt-md"
                  />
                </q-card-section>
              </q-card>
            </div>
          </template>

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
            :label="isPayToOwn ? 'Create Pay-to-Own Rental' : 'Create Rental'"
            :color="isPayToOwn ? 'purple' : 'primary'"
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
import { usersAPI, pueAPI, hubsAPI, settingsAPI, pueRentalsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const authStore = useAuthStore()

// Form data
const selectedUser = ref(null)
const selectedPUE = ref(null)
const selectedCostStructure = ref(null)
const rentalStartDate = ref(new Date().toISOString().slice(0, 16)) // datetime-local format
const isPayToOwn = ref(false)
const payToOwnPrice = ref(0)
const initialPayment = ref(0)
const notes = ref('')

// Data loading
const usersLoading = ref(false)
const puesLoading = ref(false)
const costStructuresLoading = ref(false)
const submitting = ref(false)

// Options
const userOptions = ref([])
const allUsers = ref([])
const availablePUEs = ref([])
const filteredPUEs = ref([])
const costStructureOptions = ref([])

const isFormValid = computed(() => {
  const baseValid = selectedUser.value &&
    selectedPUE.value &&
    selectedCostStructure.value

  if (isPayToOwn.value) {
    return baseValid && payToOwnPrice.value > 0
  }

  return baseValid
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

// Load available PUEs
const loadPUEs = async () => {
  try {
    puesLoading.value = true
    const hubId = authStore.currentHubId

    const response = await hubsAPI.getAvailablePUE(hubId)
    availablePUEs.value = response.data || []
    filteredPUEs.value = availablePUEs.value
  } catch (error) {
    console.error('Failed to load PUEs:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load PUE items',
      position: 'top'
    })
  } finally {
    puesLoading.value = false
  }
}

const filterPUEs = (val, update) => {
  update(() => {
    if (val === '') {
      filteredPUEs.value = availablePUEs.value
    } else {
      const needle = val.toLowerCase()
      filteredPUEs.value = availablePUEs.value.filter(p =>
        p.name?.toLowerCase().includes(needle) ||
        p.pue_type_name?.toLowerCase().includes(needle) ||
        p.pue_id?.toString().includes(needle)
      )
    }
  })
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
      pue_id: selectedPUE.value.pue_id,
      cost_structure_id: selectedCostStructure.value.cost_structure_id,
      rental_start_date: rentalStartDate.value ? new Date(rentalStartDate.value).toISOString() : undefined,
      is_pay_to_own: isPayToOwn.value,
      pay_to_own_price: isPayToOwn.value ? payToOwnPrice.value : undefined,
      initial_payment: isPayToOwn.value && initialPayment.value > 0 ? initialPayment.value : undefined,
      notes: notes.value ? [notes.value] : undefined
    }

    await pueRentalsAPI.create(rentalData)

    $q.notify({
      type: 'positive',
      message: `PUE rental created successfully${isPayToOwn.value ? ' (Pay-to-Own)' : ''}`,
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
    loadPUEs(),
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
/* Add any custom styles here */
</style>
