<template>
  <q-page class="q-pa-md">
    <div class="text-h4 q-mb-md">Accounts & Finance</div>

    <!-- Navigation Tabs -->
    <q-tabs
      v-model="activeTab"
      dense
      class="text-grey"
      active-color="primary"
      indicator-color="primary"
      align="left"
    >
      <q-tab name="summary" label="Summary" />
      <q-tab name="financial" label="Financial Transactions" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="activeTab" animated>
      <!-- Summary Tab -->
      <q-tab-panel name="summary">
        <!-- Summary Cards -->
        <div class="row q-col-gutter-md q-mb-lg">
          <div class="col-12 col-md-4">
            <q-card>
              <q-card-section>
                <div class="text-overline text-grey-7">Total Revenue</div>
                <div class="text-h4 text-positive">{{ currencySymbol }}{{ summary.total_revenue?.toFixed(2) || '0.00' }}</div>
                <div class="text-caption">{{ timePeriod }}</div>
              </q-card-section>
            </q-card>
          </div>

          <div class="col-12 col-md-4">
            <q-card>
              <q-card-section>
                <div class="text-overline text-grey-7">Outstanding Debt</div>
                <div class="text-h4 text-negative">{{ currencySymbol }}{{ summary.outstanding_debt?.toFixed(2) || '0.00' }}</div>
                <div class="text-caption">Current balance</div>
              </q-card-section>
            </q-card>
          </div>

          <div class="col-12 col-md-4">
            <q-card>
              <q-card-section>
                <div class="text-overline text-grey-7">Active Rentals</div>
                <div class="text-h4">{{ summary.active_rentals || 0 }}</div>
                <div class="text-caption">Currently ongoing</div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- Time Period Selector -->
        <div class="q-mb-md">
          <q-btn-toggle
            v-model="timePeriod"
            spread
            no-caps
            toggle-color="primary"
            :options="[
              {label: 'Day', value: 'day'},
              {label: 'Week', value: 'week'},
              {label: 'Month', value: 'month'},
              {label: 'All Time', value: 'all'}
            ]"
            @update:model-value="loadSummary"
          />
        </div>

        <!-- Users with Debt -->
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Users with Debt</div>
              </div>
              <div class="col-auto">
                <q-btn flat label="Refresh" icon="refresh" @click="loadUsersInDebt" />
              </div>
            </div>
          </q-card-section>

          <q-card-section>
            <div v-if="usersInDebt.length === 0 && !loading" class="text-center q-pa-lg text-grey-6">
              <q-icon name="check_circle" size="3em" class="q-mb-md" />
              <div class="text-h6">No users with outstanding debt</div>
              <div class="text-caption">All accounts are settled</div>
            </div>

            <q-table
              v-else
              :rows="usersInDebt"
              :columns="debtColumns"
              row-key="user_id"
              :loading="loading"
              :pagination="{ rowsPerPage: 10 }"
            >
              <template v-slot:body-cell-balance="props">
                <q-td :props="props">
                  <span :class="props.row.balance < 0 ? 'text-negative' : 'text-positive'">
                    {{ currencySymbol }}{{ props.row.balance?.toFixed(2) }}
                  </span>
                </q-td>
              </template>

              <template v-slot:body-cell-total_owed="props">
                <q-td :props="props">
                  <span class="text-negative">
                    {{ currencySymbol }}{{ props.row.total_owed?.toFixed(2) }}
                  </span>
                </q-td>
              </template>

              <template v-slot:body-cell-actions="props">
                <q-td :props="props">
                  <q-btn flat round dense icon="visibility" color="primary"
                         @click="viewUserAccount(props.row)" />
                  <q-btn flat round dense icon="payment" color="positive"
                         @click="recordPayment(props.row)" />
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </q-tab-panel>

      <!-- Financial Transactions Tab -->
      <q-tab-panel name="financial">
        <!-- Users Table -->
        <q-card class="q-mb-md">
          <q-card-section>
            <div class="row items-center q-mb-md">
              <div class="col">
                <div class="text-h6">All Users</div>
              </div>
              <div class="col-auto">
                <q-btn flat label="Refresh" icon="refresh" @click="loadAllUsers" />
              </div>
            </div>

            <!-- User Search Bar -->
            <q-input
              v-model="userSearch"
              outlined
              dense
              placeholder="Search by user ID, name, or mobile number..."
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="search" />
              </template>
              <template v-slot:append>
                <q-icon v-if="userSearch" name="clear" class="cursor-pointer" @click="userSearch = ''" />
              </template>
            </q-input>
          </q-card-section>

          <q-card-section>
            <q-table
              :rows="filteredUsers"
              :columns="userColumns"
              row-key="user_id"
              :loading="usersLoading"
              :rows-per-page-options="[10, 25, 50, 100]"
              :pagination="userPagination"
              @row-click="onUserRowClick"
              class="cursor-pointer"
            >
              <template v-slot:body-cell-balance="props">
                <q-td :props="props">
                  <span :class="props.row.balance >= 0 ? 'text-positive' : 'text-negative'">
                    {{ currencySymbol }}{{ props.row.balance?.toFixed(2) || '0.00' }}
                  </span>
                </q-td>
              </template>

              <template v-slot:body-cell-total_spent="props">
                <q-td :props="props">
                  <span class="text-positive">
                    {{ currencySymbol }}{{ props.row.total_spent?.toFixed(2) || '0.00' }}
                  </span>
                </q-td>
              </template>

              <template v-slot:body-cell-total_owed="props">
                <q-td :props="props">
                  <span class="text-negative">
                    {{ currencySymbol }}{{ props.row.total_owed?.toFixed(2) || '0.00' }}
                  </span>
                </q-td>
              </template>

              <template v-slot:body-cell-role="props">
                <q-td :props="props">
                  <q-chip
                    :color="getRoleColor(props.row.role)"
                    text-color="white"
                    dense
                    size="sm"
                  >
                    {{ props.row.role }}
                  </q-chip>
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>

        <!-- All Transactions Table -->
        <q-card>
          <q-card-section>
            <div class="row items-center q-mb-md">
              <div class="col">
                <div class="text-h6">All Transactions</div>
              </div>
              <div class="col-auto">
                <q-btn flat label="Refresh" icon="refresh" @click="loadAllTransactions" />
              </div>
            </div>

            <!-- Search Bar -->
            <q-input
              v-model="transactionSearch"
              outlined
              dense
              placeholder="Search by user ID, name, or mobile number..."
              class="q-mb-md"
            >
              <template v-slot:prepend>
                <q-icon name="search" />
              </template>
              <template v-slot:append>
                <q-icon v-if="transactionSearch" name="clear" class="cursor-pointer" @click="transactionSearch = ''" />
              </template>
            </q-input>
          </q-card-section>

          <q-card-section>
            <q-table
              :rows="filteredTransactions"
              :columns="transactionColumns"
              row-key="transaction_id"
              :loading="transactionsLoading"
              :rows-per-page-options="[10, 25, 50, 100]"
              :pagination="transactionPagination"
              @row-click="onTransactionRowClick"
              class="cursor-pointer"
            >
              <template v-slot:body-cell-amount="props">
                <q-td :props="props">
                  <span :class="props.row.transaction_type === 'charge' ? 'text-negative' : 'text-positive'">
                    {{ props.row.transaction_type === 'charge' ? '-' : '+' }}{{ currencySymbol }}{{ Math.abs(props.row.amount)?.toFixed(2) }}
                  </span>
                </q-td>
              </template>

              <template v-slot:body-cell-transaction_type="props">
                <q-td :props="props">
                  <q-chip
                    :color="props.row.transaction_type === 'charge' ? 'negative' : 'positive'"
                    text-color="white"
                    dense
                    size="sm"
                  >
                    {{ props.row.transaction_type }}
                  </q-chip>
                </q-td>
              </template>

              <template v-slot:body-cell-timestamp="props">
                <q-td :props="props">
                  {{ formatTimestamp(props.row.timestamp) }}
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </q-tab-panel>
    </q-tab-panels>

    <!-- Record Payment Dialog -->
    <q-dialog v-model="showPaymentDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Record Payment</div>
          <div class="text-subtitle2">User: {{ selectedUser?.user }}</div>
          <div class="text-caption">Current Debt: {{ currencySymbol }}{{ selectedUser?.total_owed?.toFixed(2) }}</div>
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <q-input
            v-model.number="paymentAmount"
            type="number"
            label="Payment Amount"
            :prefix="currencySymbol"
            step="0.01"
            :rules="[val => val > 0 || 'Must be greater than 0']"
          />
          <q-input
            v-model="paymentDescription"
            label="Description"
            hint="Optional note about the payment"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn flat label="Record Payment" color="primary" @click="submitPayment" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { accountsAPI, hubsAPI, settingsAPI } from 'src/services/api'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'stores/auth'
import { useRouter } from 'vue-router'

const $q = useQuasar()
const authStore = useAuthStore()
const router = useRouter()
const hubId = authStore.user?.hub_id

const loading = ref(false)
const timePeriod = ref('all')
const activeTab = ref('summary')

// Hub settings for currency
const hubSettings = ref({ default_currency: 'USD' })

// Currency helper functions
const getCurrencySymbol = (currency) => {
  const symbols = {
    'USD': '$',
    'GBP': '£',
    'EUR': '€',
    'MWK': 'MK'
  }
  return symbols[currency] || currency
}

const currencySymbol = computed(() => {
  return getCurrencySymbol(hubSettings.value.default_currency)
})

// Summary
const summary = ref({
  total_revenue: 0,
  outstanding_debt: 0,
  active_rentals: 0,
  total_users: 0
})

// Users in Debt
const usersInDebt = ref([])
const showPaymentDialog = ref(false)
const selectedUser = ref(null)
const paymentAmount = ref(0)
const paymentDescription = ref('')

const debtColumns = [
  { name: 'user', label: 'User', field: 'user', align: 'left' },
  { name: 'balance', label: 'Balance', field: 'balance', align: 'right' },
  { name: 'total_owed', label: 'Amount Owed', field: 'total_owed', align: 'right' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const loadSummary = async () => {
  if (!hubId) return
  try {
    loading.value = true
    const response = await accountsAPI.getHubSummary(hubId, { time_period: timePeriod.value })
    summary.value = response.data
  } catch (error) {
    console.error('Failed to load summary:', error)
    $q.notify({ type: 'negative', message: 'Failed to load financial summary', position: 'top' })
  } finally {
    loading.value = false
  }
}

const loadUsersInDebt = async () => {
  try {
    loading.value = true
    const response = await accountsAPI.getUsersInDebt({ hub_id: hubId })
    console.log('Users in debt response:', response.data)

    // Handle different response structures
    if (response.data && Array.isArray(response.data.users)) {
      usersInDebt.value = response.data.users
    } else if (response.data && Array.isArray(response.data)) {
      usersInDebt.value = response.data
    } else {
      usersInDebt.value = []
    }

    console.log('Users in debt count:', usersInDebt.value.length)
  } catch (error) {
    console.error('Failed to load users in debt:', error)
    usersInDebt.value = []
    $q.notify({ type: 'negative', message: 'Failed to load users with debt', position: 'top' })
  } finally {
    loading.value = false
  }
}

const viewUserAccount = (user) => {
  router.push({ name: 'user-detail', params: { id: user.user_id } })
}

const recordPayment = (user) => {
  selectedUser.value = user
  paymentAmount.value = user.total_owed
  paymentDescription.value = ''
  showPaymentDialog.value = true
}

const submitPayment = async () => {
  if (!selectedUser.value || paymentAmount.value <= 0) return

  try {
    await accountsAPI.createTransaction(selectedUser.value.user_id, {
      transaction_type: 'payment',
      amount: paymentAmount.value,
      description: paymentDescription.value || `Payment received`
    })

    $q.notify({ type: 'positive', message: 'Payment recorded successfully', position: 'top' })
    showPaymentDialog.value = false
    await loadUsersInDebt()
    await loadSummary()
  } catch (error) {
    console.error('Failed to record payment:', error)
    $q.notify({ type: 'negative', message: 'Failed to record payment', position: 'top' })
  }
}

// Financial Transactions Tab - Users
const allUsers = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const userPagination = ref({
  sortBy: 'user_id',
  descending: false,
  page: 1,
  rowsPerPage: 25
})

const userColumns = [
  { name: 'user_id', label: 'User ID', field: 'user_id', align: 'left', sortable: true },
  { name: 'user_name', label: 'Name', field: 'user_name', align: 'left', sortable: true },
  { name: 'mobile_number', label: 'Mobile', field: 'mobile_number', align: 'left', sortable: true },
  { name: 'role', label: 'Role', field: 'role', align: 'center', sortable: true },
  { name: 'balance', label: 'Balance', field: 'balance', align: 'right', sortable: true },
  { name: 'total_spent', label: 'Total Spent', field: 'total_spent', align: 'right', sortable: true },
  { name: 'total_owed', label: 'Total Owed', field: 'total_owed', align: 'right', sortable: true }
]

const filteredUsers = computed(() => {
  if (!userSearch.value) return allUsers.value

  const search = userSearch.value.toLowerCase()
  return allUsers.value.filter(u =>
    u.user_name?.toLowerCase().includes(search) ||
    String(u.user_id || '').toLowerCase().includes(search) ||
    u.mobile_number?.toLowerCase().includes(search)
  )
})

const getRoleColor = (role) => {
  switch (role?.toUpperCase()) {
    case 'SUPERADMIN': return 'red'
    case 'ADMIN': return 'orange'
    case 'USER': return 'blue'
    default: return 'grey'
  }
}

// Financial Transactions Tab - Transactions
const allTransactions = ref([])
const transactionsLoading = ref(false)
const transactionSearch = ref('')
const transactionPagination = ref({
  sortBy: 'timestamp',
  descending: true,
  page: 1,
  rowsPerPage: 25
})

const transactionColumns = [
  { name: 'timestamp', label: 'Date', field: 'timestamp', align: 'left', sortable: true },
  { name: 'user_name', label: 'User Name', field: 'user_name', align: 'left', sortable: true },
  { name: 'user_id', label: 'User ID', field: 'user_id', align: 'left', sortable: true },
  { name: 'mobile_number', label: 'Mobile', field: 'mobile_number', align: 'left', sortable: true },
  { name: 'transaction_type', label: 'Type', field: 'transaction_type', align: 'center', sortable: true },
  { name: 'amount', label: 'Amount', field: 'amount', align: 'right', sortable: true },
  { name: 'description', label: 'Description', field: 'description', align: 'left' }
]

const filteredTransactions = computed(() => {
  if (!transactionSearch.value) return allTransactions.value

  const search = transactionSearch.value.toLowerCase()
  return allTransactions.value.filter(t =>
    t.user_name?.toLowerCase().includes(search) ||
    String(t.user_id || '').toLowerCase().includes(search) ||
    t.mobile_number?.toLowerCase().includes(search)
  )
})

const formatTimestamp = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString() + ' UTC'
}

const loadAllTransactions = async () => {
  if (!hubId) return

  try {
    transactionsLoading.value = true

    // Get all users at this hub
    const usersResponse = await hubsAPI.getUsers(hubId)
    const users = usersResponse.data || []

    // Load transactions for all users
    const transactionPromises = users.map(async (user) => {
      try {
        const response = await accountsAPI.getUserTransactions(user.user_id)
        return response.data.transactions.map(t => ({
          ...t,
          user_name: user.Name || user.username || `User ${user.user_id}`,
          user_id: user.user_id,
          mobile_number: user.mobile_number
        }))
      } catch (error) {
        console.error(`Failed to load transactions for user ${user.user_id}:`, error)
        return []
      }
    })

    const allTransactionArrays = await Promise.all(transactionPromises)
    const flatTransactions = allTransactionArrays.flat()

    // Sort by timestamp descending (newest first)
    flatTransactions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

    allTransactions.value = flatTransactions
  } catch (error) {
    console.error('Failed to load transactions:', error)
    $q.notify({ type: 'negative', message: 'Failed to load transactions', position: 'top' })
  } finally {
    transactionsLoading.value = false
  }
}

const onTransactionRowClick = (_evt, row) => {
  router.push({ name: 'user-detail', params: { id: row.user_id } })
}

const loadAllUsers = async () => {
  if (!hubId) return

  try {
    usersLoading.value = true

    // Get all users at this hub
    const usersResponse = await hubsAPI.getUsers(hubId)
    const users = usersResponse.data || []

    // Load account information for each user
    const userPromises = users.map(async (user) => {
      try {
        const accountResponse = await accountsAPI.getUserAccount(user.user_id)
        return {
          user_id: user.user_id,
          user_name: user.Name || user.username || `User ${user.user_id}`,
          mobile_number: user.mobile_number,
          email: user.email,
          role: user.role,
          balance: accountResponse.data.balance || 0,
          total_spent: accountResponse.data.total_spent || 0,
          total_owed: accountResponse.data.total_owed || 0
        }
      } catch (error) {
        console.error(`Failed to load account for user ${user.user_id}:`, error)
        return {
          user_id: user.user_id,
          user_name: user.Name || user.username || `User ${user.user_id}`,
          mobile_number: user.mobile_number,
          email: user.email,
          role: user.role,
          balance: 0,
          total_spent: 0,
          total_owed: 0
        }
      }
    })

    allUsers.value = await Promise.all(userPromises)
  } catch (error) {
    console.error('Failed to load users:', error)
    $q.notify({ type: 'negative', message: 'Failed to load users', position: 'top' })
  } finally {
    usersLoading.value = false
  }
}

const onUserRowClick = (_evt, row) => {
  router.push({ name: 'user-detail', params: { id: row.user_id } })
}

// Watch for tab changes
watch(activeTab, (newTab) => {
  if (newTab === 'financial') {
    if (allUsers.value.length === 0) {
      loadAllUsers()
    }
    if (allTransactions.value.length === 0) {
      loadAllTransactions()
    }
  }
})

const loadHubSettings = async () => {
  if (!hubId) return
  try {
    const response = await settingsAPI.getHubSettings(hubId)
    if (response.data) {
      hubSettings.value = response.data
    }
  } catch (error) {
    console.error('Failed to load hub settings:', error)
    // Keep default currency if failed to load
  }
}

onMounted(() => {
  loadHubSettings()
  loadSummary()
  loadUsersInDebt()
  if (activeTab.value === 'financial') {
    loadAllTransactions()
  }
})
</script>
