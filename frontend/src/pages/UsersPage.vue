<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="col-12 col-sm-auto">
        <div class="text-h5">Users</div>
      </div>
      <div class="col-12 col-sm row items-center q-gutter-sm">
        <HubFilter v-model="selectedHub" @change="onHubChange" />
        <q-btn
          label="Add User"
          icon="add"
          color="primary"
          @click="openCreateDialog"
          size="sm"
          class="col-12 col-sm-auto"
        />
      </div>
    </div>

    <q-card>
      <q-card-section>
        <q-table
          :rows="users"
          :columns="columns"
          row-key="user_id"
          :loading="loading"
          :filter="filter"
          @row-click="onUserRowClick"
          class="cursor-pointer"
          no-data-label="No customers found - add your first customer to get started!"
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

          <template v-slot:body-cell-user_access_level="props">
            <q-td :props="props">
              <q-badge
                :color="getRoleColor(props.row.user_access_level)"
                :label="getRoleLabel(props.row.user_access_level)"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                v-if="authStore.isAdmin"
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click.stop="editUser(props.row)"
              />
              <q-btn
                v-if="authStore.isSuperAdmin"
                flat
                round
                dense
                icon="lock_reset"
                color="orange"
                @click.stop="openResetPasswordDialog(props.row)"
              >
                <q-tooltip>Reset Password</q-tooltip>
              </q-btn>
              <q-btn
                v-if="authStore.isSuperAdmin"
                flat
                round
                dense
                icon="delete"
                color="negative"
                @click.stop="deleteUser(props.row)"
              />
              <q-btn
                flat
                round
                dense
                icon="key"
                color="info"
                @click.stop="manageHubAccess(props.row)"
              >
                <q-tooltip>Manage Hub Access</q-tooltip>
              </q-btn>
              <q-btn
                flat
                round
                dense
                icon="subscriptions"
                color="positive"
                @click.stop="manageSubscription(props.row)"
              >
                <q-tooltip>Manage Subscription</q-tooltip>
              </q-btn>
              <q-btn
                flat
                round
                dense
                icon="account_balance_wallet"
                color="primary"
                @click.stop="viewAccountDetails(props.row)"
              >
                <q-tooltip>View Account & Credit</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Create/Edit Dialog -->
    <q-dialog v-model="showCreateDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">{{ editingUser ? 'Edit Customer' : 'Create Customer' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveUser" class="q-gutter-md">
            <div class="row q-gutter-sm">
              <div class="col-12 col-sm-6">
                <q-input
                  v-model="formData.first_names"
                  label="First Name(s) *"
                  outlined
                  :rules="[val => !!val || 'First name is required']"
                  hint="Given name(s)"
                />
              </div>
              <div class="col-12 col-sm-6">
                <q-input
                  v-model="formData.last_name"
                  label="Last Name *"
                  outlined
                  :rules="[val => !!val || 'Last name is required']"
                  hint="Family name / Surname"
                />
              </div>
            </div>

            <q-input
              v-model="formData.username"
              label="Username *"
              outlined
              :rules="[val => !!val || 'Username is required']"
              hint="Used for login"
            />

            <q-input
              v-if="!editingUser"
              v-model="formData.password"
              label="Password *"
              :type="showPassword ? 'text' : 'password'"
              outlined
              :rules="[
                val => !!val || 'Password is required',
                val => val.length >= 8 || 'Password must be at least 8 characters'
              ]"
              hint="Minimum 8 characters required"
            >
              <template v-slot:append>
                <q-btn
                  flat
                  round
                  dense
                  :icon="showPassword ? 'visibility_off' : 'visibility'"
                  @click="showPassword = !showPassword"
                  size="sm"
                >
                  <q-tooltip>{{ showPassword ? 'Hide password' : 'Show password' }}</q-tooltip>
                </q-btn>
                <q-btn
                  flat
                  round
                  dense
                  icon="casino"
                  @click="generatePassword"
                  color="primary"
                  size="sm"
                >
                  <q-tooltip>Generate random password</q-tooltip>
                </q-btn>
              </template>
            </q-input>

            <q-select
              v-model="formData.hub_id"
              :options="hubOptions"
              option-value="hub_id"
              option-label="what_three_word_location"
              emit-value
              map-options
              :display-value="(authStore.role === 'admin' || authStore.role === 'hub_admin') ? selectedHubName : undefined"
              label="Hub *"
              outlined
              :rules="[val => !!val || 'Hub is required']"
              :disable="authStore.role === 'admin' || authStore.role === 'hub_admin'"
              :hint="authStore.role === 'admin' || authStore.role === 'hub_admin' ? 'Automatically set to your hub' : 'Primary hub for this user'"
            />

            <q-select
              v-model="formData.user_access_level"
              :options="roleOptions"
              label="Access Level *"
              outlined
              emit-value
              map-options
              :rules="[val => !!val || 'Access level is required']"
              hint="user, admin, superadmin, or data_admin"
            />

            <q-input
              v-model="formData.mobile_number"
              label="Mobile Number"
              outlined
              hint="Optional - for contact and notifications"
            />

            <q-input
              v-model="formData.users_identification_document_number"
              label="ID Document Number *"
              outlined
              hint="Required - for customer verification"
              :rules="[val => !!val || 'ID document number is required']"
            />

            <!-- ID Document Photo Upload -->
            <div class="q-mb-md">
              <div class="text-subtitle2 q-mb-sm">ID Document Photo</div>
              <q-file
                v-model="idDocumentPhoto"
                outlined
                accept="image/*"
                capture="environment"
                label="Upload or Take Photo"
                hint="Optional - take a photo or upload from device"
                :clearable="true"
                @update:model-value="onPhotoSelected"
              >
                <template v-slot:prepend>
                  <q-icon name="photo_camera" />
                </template>
              </q-file>

              <!-- Photo Preview -->
              <div v-if="photoPreview" class="q-mt-sm">
                <q-img
                  :src="photoPreview"
                  style="max-width: 200px; max-height: 200px"
                  class="rounded-borders"
                />
              </div>
            </div>

            <q-input
              v-model="formData.physical_address"
              label="Physical Address"
              type="textarea"
              outlined
              rows="2"
              hint="Optional - physical location/address"
            />

            <q-input
              v-model="formData.date_of_birth"
              label="Date of Birth"
              outlined
              type="date"
              hint="Optional - customer's birth date"
            />

            <q-select
              v-model="formData.gesi_status"
              :options="gesiStatusOptions"
              label="GESI Status"
              outlined
              clearable
              hint="Optional - Gender Equality & Social Inclusion category"
            />

            <q-select
              v-model="formData.business_category"
              :options="businessCategoryOptions"
              label="Business Category"
              outlined
              clearable
              hint="Optional - Size/type of business"
            />

            <q-input
              v-model.number="formData.monthly_energy_expenditure"
              label="Monthly Energy Expenditure"
              type="number"
              outlined
              prefix="$"
              hint="Optional - Current monthly spending on energy/power"
            />

            <q-select
              v-model="formData.main_reason_for_signup"
              :options="signupReasonOptions"
              label="Main Reason for Signing Up"
              outlined
              clearable
              hint="Optional - Primary motivation for joining"
            />

            <div class="row justify-end q-gutter-sm">
              <q-btn label="Cancel" flat v-close-popup />
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

    <!-- Hub Access Dialog -->
    <q-dialog v-model="showHubAccessDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Manage Hub Access</div>
          <div class="text-subtitle2">{{ selectedUser?.username }}</div>
        </q-card-section>

        <q-card-section>
          <q-list>
            <q-item v-for="hub in hubOptions" :key="hub.hub_id">
              <q-item-section>
                <q-item-label>{{ hub.what_three_word_location }}</q-item-label>
                <q-item-label caption>{{ hub.country }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-toggle
                  :model-value="hasHubAccess(hub.hub_id)"
                  @update:model-value="toggleHubAccess(hub.hub_id, $event)"
                />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn label="Close" flat v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Reset Password Dialog -->
    <ResetPasswordDialog
      v-model="showResetPasswordDialog"
      :user="selectedUserForReset"
      @success="onPasswordResetSuccess"
    />
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { usersAPI, hubsAPI, settingsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'
import { useRouter, useRoute } from 'vue-router'
import HubFilter from 'src/components/HubFilter.vue'
import ResetPasswordDialog from 'src/components/ResetPasswordDialog.vue'

const $q = useQuasar()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const users = ref([])
const hubOptions = ref([])
const loading = ref(false)
const filter = ref('')
const selectedHub = ref(null)
const showCreateDialog = ref(false)
const showHubAccessDialog = ref(false)
const showResetPasswordDialog = ref(false)
const editingUser = ref(null)
const selectedUserForReset = ref(null)

// Customer field options for dropdowns
const gesiStatusOptions = ref([])
const businessCategoryOptions = ref([])
const signupReasonOptions = ref([])
const selectedUser = ref(null)
const saving = ref(false)

const formData = ref({
  user_id: null,
  first_names: '',
  last_name: '',
  username: '',
  password: '',
  hub_id: null,
  user_access_level: 'user',
  mobile_number: '',
  users_identification_document_number: '',
  physical_address: '',
  date_of_birth: null,
  gesi_status: null,
  business_category: null,
  monthly_energy_expenditure: null,
  main_reason_for_signup: null
})

const showPassword = ref(false)
const idDocumentPhoto = ref(null)
const photoPreview = ref(null)

// Handle photo selection
const onPhotoSelected = (file) => {
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      photoPreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  } else {
    photoPreview.value = null
  }
}

// Generate a random secure password
const generatePassword = () => {
  const length = 12
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const lowercase = 'abcdefghijklmnopqrstuvwxyz'
  const numbers = '0123456789'
  const symbols = '!@#$%^&*'
  const allChars = uppercase + lowercase + numbers + symbols

  let password = ''
  // Ensure at least one of each type
  password += uppercase[Math.floor(Math.random() * uppercase.length)]
  password += lowercase[Math.floor(Math.random() * lowercase.length)]
  password += numbers[Math.floor(Math.random() * numbers.length)]
  password += symbols[Math.floor(Math.random() * symbols.length)]

  // Fill the rest randomly
  for (let i = password.length; i < length; i++) {
    password += allChars[Math.floor(Math.random() * allChars.length)]
  }

  // Shuffle the password
  password = password.split('').sort(() => Math.random() - 0.5).join('')

  formData.value.password = password
  showPassword.value = true // Show the generated password

  $q.notify({
    type: 'positive',
    message: 'Password generated! Make sure to copy it.',
    position: 'top',
    timeout: 3000
  })
}

const getRoleLabel = (role) => {
  const labels = {
    user: 'Customer',
    hub_admin: 'Hub Admin',
    admin: 'Admin',
    superadmin: 'Super Admin',
    data_admin: 'Data Admin',
    battery: 'Battery'
  }
  return labels[role] || role
}

const selectedHubName = computed(() => {
  if (!formData.value.hub_id || !hubOptions.value.length) return ''
  const hub = hubOptions.value.find(h => h.hub_id === formData.value.hub_id)
  return hub ? hub.what_three_word_location : ''
})

const roleOptions = computed(() => {
  // Hub admins can only create customers
  if (authStore.role === 'hub_admin') {
    return [
      { label: 'Customer', value: 'user' }
    ]
  }

  // Admins can create all roles except superadmin
  if (authStore.role === 'admin') {
    return [
      { label: 'Customer', value: 'user' },
      { label: 'Hub Admin', value: 'hub_admin' },
      { label: 'Admin', value: 'admin' },
      { label: 'Data Admin', value: 'data_admin' }
    ]
  }

  // Superadmins can create all roles
  return [
    { label: 'Customer', value: 'user' },
    { label: 'Hub Admin', value: 'hub_admin' },
    { label: 'Admin', value: 'admin' },
    { label: 'Super Admin', value: 'superadmin' },
    { label: 'Data Admin', value: 'data_admin' }
  ]
})

const columns = [
  { name: 'user_id', label: 'ID', field: 'user_id', align: 'left', sortable: true },
  { name: 'username', label: 'Username', field: 'username', align: 'left', sortable: true },
  { name: 'Name', label: 'Name', field: 'Name', align: 'left', sortable: true },
  { name: 'mobile_number', label: 'Mobile', field: 'mobile_number', align: 'left' },
  { name: 'user_access_level', label: 'Role', field: 'user_access_level', align: 'center', sortable: true },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const getRoleColor = (role) => {
  const colors = {
    user: 'grey',
    hub_admin: 'blue-grey',
    admin: 'primary',
    superadmin: 'purple',
    data_admin: 'info',
    battery: 'orange'
  }
  return colors[role] || 'grey'
}

const loadUsers = async () => {
  loading.value = true
  try {
    if (selectedHub.value) {
      // Load users for selected hub only
      const usersResponse = await hubsAPI.getUsers(selectedHub.value)
      users.value = usersResponse.data
    } else {
      // Note: The API doesn't have a list all users endpoint
      // We'll need to load users from hubs
      const hubsResponse = await hubsAPI.list()
      const allUsers = new Map()

      for (const hub of hubsResponse.data) {
        const usersResponse = await hubsAPI.getUsers(hub.hub_id)
        usersResponse.data.forEach(user => {
          allUsers.set(user.user_id, user)
        })
      }

      users.value = Array.from(allUsers.values())
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load users',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const onHubChange = (hubId) => {
  selectedHub.value = hubId
  loadUsers()
}

const loadHubs = async () => {
  try {
    const response = await hubsAPI.list()
    hubOptions.value = response.data
  } catch (error) {
    console.error('Failed to load hubs:', error)
  }
}

const editUser = (user) => {
  editingUser.value = user
  formData.value = { ...user, password: '' }
  showCreateDialog.value = true
}

const saveUser = async () => {
  saving.value = true
  try {
    let userId
    if (editingUser.value) {
      const updateData = { ...formData.value }
      if (!updateData.password) {
        delete updateData.password
      }
      await usersAPI.update(editingUser.value.user_id, updateData)
      userId = editingUser.value.user_id
      $q.notify({
        type: 'positive',
        message: 'Customer updated successfully',
        position: 'top'
      })
    } else {
      const response = await usersAPI.create(formData.value)
      userId = response.data.user_id
      $q.notify({
        type: 'positive',
        message: 'Customer created successfully',
        position: 'top'
      })
    }

    // Upload photo if one was selected
    if (idDocumentPhoto.value && userId) {
      try {
        await usersAPI.uploadIdPhoto(userId, idDocumentPhoto.value)
        $q.notify({
          type: 'positive',
          message: 'ID document photo uploaded successfully',
          position: 'top'
        })
      } catch (photoError) {
        console.error('Photo upload error:', photoError)
        $q.notify({
          type: 'warning',
          message: 'Customer saved but photo upload failed',
          position: 'top'
        })
      }
    }

    showCreateDialog.value = false
    resetForm()
    loadUsers()
  } catch (error) {
    console.error('Customer creation error:', error)
    console.error('Error response:', error.response?.data)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to save customer',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const deleteUser = (user) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Are you sure you want to delete customer "${user.username}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await usersAPI.delete(user.user_id)
      $q.notify({
        type: 'positive',
        message: 'Customer deleted successfully',
        position: 'top'
      })
      loadUsers()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to delete user',
        position: 'top'
      })
    }
  })
}

const openResetPasswordDialog = (user) => {
  selectedUserForReset.value = user
  showResetPasswordDialog.value = true
}

const onPasswordResetSuccess = () => {
  showResetPasswordDialog.value = false
  selectedUserForReset.value = null
}

const onUserRowClick = (_evt, row) => {
  router.push({ name: 'user-detail', params: { id: row.user_id } })
}

const manageHubAccess = async (user) => {
  selectedUser.value = user
  // Load the user's detailed info to get accessible_hubs
  try {
    const response = await usersAPI.get(user.user_id)
    selectedUser.value = response.data
  } catch (error) {
    console.error('Failed to load user details:', error)
  }
  showHubAccessDialog.value = true
}

const manageSubscription = (user) => {
  // Navigate to user detail page which has subscription management
  router.push({ name: 'user-detail', params: { id: user.user_id } })
}

const viewAccountDetails = (user) => {
  // Navigate to user detail page which shows account details
  router.push({ name: 'user-detail', params: { id: user.user_id } })
}

const hasHubAccess = (hubId) => {
  if (!selectedUser.value) return false

  // For DATA_ADMIN users, check accessible_hubs
  if (selectedUser.value.user_access_level === 'data_admin' && selectedUser.value.accessible_hubs) {
    return selectedUser.value.accessible_hubs.some(hub => hub.hub_id === hubId)
  }

  // For other users, check if it's their primary hub
  return selectedUser.value.hub_id === hubId
}

const toggleHubAccess = async (hubId, hasAccess) => {
  try {
    if (hasAccess) {
      await usersAPI.grantHubAccess(selectedUser.value.user_id, hubId)
      $q.notify({
        type: 'positive',
        message: 'Hub access granted',
        position: 'top'
      })
    } else {
      await usersAPI.revokeHubAccess(selectedUser.value.user_id, hubId)
      $q.notify({
        type: 'positive',
        message: 'Hub access revoked',
        position: 'top'
      })
    }

    // Reload user data to reflect changes
    const response = await usersAPI.get(selectedUser.value.user_id)
    selectedUser.value = response.data

    // Also reload the users list
    await loadUsers()
  } catch (error) {
    console.error('Hub access error:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to update hub access',
      position: 'top'
    })
  }
}

const openCreateDialog = () => {
  resetForm()
  // Auto-select hub for admin and hub_admin users (not superadmin)
  if (authStore.role === 'admin' || authStore.role === 'hub_admin') {
    formData.value.hub_id = authStore.currentHubId
  }
  showCreateDialog.value = true
}

const resetForm = () => {
  formData.value = {
    user_id: null,
    name: '',
    username: '',
    password: '',
    hub_id: null,
    user_access_level: 'user',
    mobile_number: '',
    users_identification_document_number: '',
    address: ''
  }
  showPassword.value = false
  editingUser.value = null
  idDocumentPhoto.value = null
  photoPreview.value = null
}

// Load customer field options for dropdowns
const loadCustomerFieldOptions = async () => {
  try {
    const response = await settingsAPI.getCustomerFieldOptions({
      hub_id: authStore.user?.hub_id
    })
    const options = response.data || []

    // Extract and map options to dropdown format
    gesiStatusOptions.value = options
      .filter(opt => opt.field_name === 'gesi_status' && opt.is_active)
      .sort((a, b) => a.sort_order - b.sort_order)
      .map(opt => opt.option_value)

    businessCategoryOptions.value = options
      .filter(opt => opt.field_name === 'business_category' && opt.is_active)
      .sort((a, b) => a.sort_order - b.sort_order)
      .map(opt => opt.option_value)

    signupReasonOptions.value = options
      .filter(opt => opt.field_name === 'main_reason_for_signup' && opt.is_active)
      .sort((a, b) => a.sort_order - b.sort_order)
      .map(opt => opt.option_value)
  } catch (error) {
    console.error('Failed to load customer field options:', error)
  }
}

onMounted(() => {
  loadUsers()
  loadHubs()
  loadCustomerFieldOptions()

  // Check if we should auto-open the create user dialog
  if (route.query.action === 'create') {
    showCreateDialog.value = true
  }
})
</script>
