<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h4">Users</div>
      </div>
      <div class="col-auto row items-center q-gutter-sm">
        <HubFilter v-model="selectedHub" @change="onHubChange" />
        <q-btn
          label="Add User"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
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
          no-data-label="No users found - add your first user to get started!"
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
                :label="props.row.user_access_level"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click="editUser(props.row)"
              />
              <q-btn
                v-if="authStore.isSuperAdmin"
                flat
                round
                dense
                icon="delete"
                color="negative"
                @click="deleteUser(props.row)"
              />
              <q-btn
                flat
                round
                dense
                icon="key"
                color="info"
                @click="manageHubAccess(props.row)"
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
          <div class="text-h6">{{ editingUser ? 'Edit User' : 'Create User' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveUser" class="q-gutter-md">
            <q-input
              v-if="!editingUser"
              v-model.number="formData.user_id"
              label="User ID"
              type="number"
              outlined
              :rules="[val => !!val || 'User ID is required']"
              hint="Unique identifier for this user"
            />

            <q-input
              v-model="formData.name"
              label="Name"
              outlined
              :rules="[val => !!val || 'Name is required']"
            />

            <q-input
              v-model="formData.username"
              label="Username"
              outlined
              :rules="[val => !!val || 'Username is required']"
            />

            <q-input
              v-if="!editingUser"
              v-model="formData.password"
              label="Password"
              type="password"
              outlined
              :rules="[val => !!val || 'Password is required']"
            />

            <q-select
              v-model="formData.hub_id"
              :options="hubOptions"
              option-value="hub_id"
              option-label="what_three_word_location"
              emit-value
              map-options
              label="Hub"
              outlined
              :rules="[val => !!val || 'Hub is required']"
            />

            <q-select
              v-model="formData.user_access_level"
              :options="roleOptions"
              label="Access Level"
              outlined
              :rules="[val => !!val || 'Access level is required']"
            />

            <q-input
              v-model="formData.mobile_number"
              label="Mobile Number"
              outlined
            />

            <q-input
              v-model="formData.users_identification_document_number"
              label="ID Document Number"
              outlined
            />

            <q-input
              v-model="formData.address"
              label="Address"
              type="textarea"
              outlined
              rows="2"
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
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { usersAPI, hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import HubFilter from 'src/components/HubFilter.vue'

const $q = useQuasar()
const authStore = useAuthStore()
const router = useRouter()

const users = ref([])
const hubOptions = ref([])
const loading = ref(false)
const filter = ref('')
const selectedHub = ref(null)
const showCreateDialog = ref(false)
const showHubAccessDialog = ref(false)
const editingUser = ref(null)
const selectedUser = ref(null)
const saving = ref(false)

const formData = ref({
  user_id: null,
  name: '',
  username: '',
  password: '',
  hub_id: null,
  user_access_level: 'user',
  mobile_number: '',
  users_identification_document_number: '',
  address: ''
})

const roleOptions = ['user', 'admin', 'superadmin', 'data_admin']

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
    admin: 'primary',
    superadmin: 'purple',
    data_admin: 'info'
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
    if (editingUser.value) {
      const updateData = { ...formData.value }
      if (!updateData.password) {
        delete updateData.password
      }
      await usersAPI.update(editingUser.value.user_id, updateData)
      $q.notify({
        type: 'positive',
        message: 'User updated successfully',
        position: 'top'
      })
    } else {
      await usersAPI.create(formData.value)
      $q.notify({
        type: 'positive',
        message: 'User created successfully',
        position: 'top'
      })
    }
    showCreateDialog.value = false
    resetForm()
    loadUsers()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to save user',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const deleteUser = (user) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Are you sure you want to delete user "${user.username}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await usersAPI.delete(user.user_id)
      $q.notify({
        type: 'positive',
        message: 'User deleted successfully',
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
  editingUser.value = null
}

onMounted(() => {
  loadUsers()
  loadHubs()
})
</script>
