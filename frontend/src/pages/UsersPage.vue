<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h4">Users</div>
      </div>
      <div class="col-auto">
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

          <template v-slot:body-cell-role="props">
            <q-td :props="props">
              <q-badge
                :color="getRoleColor(props.row.role)"
                :label="props.row.role"
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
              v-model="formData.username"
              label="Username"
              outlined
              :rules="[val => !!val || 'Username is required']"
            />

            <q-input
              v-model="formData.email"
              label="Email"
              type="email"
              outlined
              :rules="[val => !!val || 'Email is required']"
            />

            <q-input
              v-model="formData.full_name"
              label="Full Name"
              outlined
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
              v-model="formData.role"
              :options="roleOptions"
              label="Role"
              outlined
              :rules="[val => !!val || 'Role is required']"
            />

            <q-input
              v-model="formData.phone"
              label="Phone"
              outlined
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
            <q-item v-for="hub in hubOptions" :key="hub.id">
              <q-item-section>
                <q-item-label>{{ hub.name }}</q-item-label>
                <q-item-label caption>{{ hub.location }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-toggle
                  :model-value="hasHubAccess(hub.id)"
                  @update:model-value="toggleHubAccess(hub.id, $event)"
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

const $q = useQuasar()
const authStore = useAuthStore()

const users = ref([])
const hubOptions = ref([])
const loading = ref(false)
const filter = ref('')
const showCreateDialog = ref(false)
const showHubAccessDialog = ref(false)
const editingUser = ref(null)
const selectedUser = ref(null)
const saving = ref(false)

const formData = ref({
  username: '',
  email: '',
  full_name: '',
  password: '',
  role: 'user',
  phone: ''
})

const roleOptions = ['user', 'admin', 'superadmin', 'data_admin']

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true },
  { name: 'username', label: 'Username', field: 'username', align: 'left', sortable: true },
  { name: 'email', label: 'Email', field: 'email', align: 'left', sortable: true },
  { name: 'full_name', label: 'Full Name', field: 'full_name', align: 'left' },
  { name: 'role', label: 'Role', field: 'role', align: 'center', sortable: true },
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
    // Note: The API doesn't have a list all users endpoint
    // We'll need to load users from hubs
    const hubsResponse = await hubsAPI.list()
    const allUsers = new Map()

    for (const hub of hubsResponse.data) {
      const usersResponse = await hubsAPI.getUsers(hub.id)
      usersResponse.data.forEach(user => {
        allUsers.set(user.id, user)
      })
    }

    users.value = Array.from(allUsers.values())
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
      await usersAPI.update(editingUser.value.id, updateData)
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
      await usersAPI.delete(user.id)
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

const manageHubAccess = (user) => {
  selectedUser.value = user
  showHubAccessDialog.value = true
}

const hasHubAccess = (hubId) => {
  // This would need to be implemented based on your API
  return false
}

const toggleHubAccess = async (hubId, hasAccess) => {
  try {
    if (hasAccess) {
      await usersAPI.grantHubAccess(selectedUser.value.id, hubId)
      $q.notify({
        type: 'positive',
        message: 'Hub access granted',
        position: 'top'
      })
    } else {
      await usersAPI.revokeHubAccess(selectedUser.value.id, hubId)
      $q.notify({
        type: 'positive',
        message: 'Hub access revoked',
        position: 'top'
      })
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to update hub access',
      position: 'top'
    })
  }
}

const resetForm = () => {
  formData.value = {
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'user',
    phone: ''
  }
  editingUser.value = null
}

onMounted(() => {
  loadUsers()
  loadHubs()
})
</script>
