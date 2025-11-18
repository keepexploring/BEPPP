<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-h4">Hubs</div>
      </div>
      <div class="col-auto">
        <q-btn
          v-if="authStore.isAdmin"
          label="Add Hub"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <q-card>
      <q-card-section>
        <q-table
          :rows="hubs"
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

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn
                flat
                round
                dense
                icon="visibility"
                color="primary"
                :to="{ name: 'hub-detail', params: { id: props.row.id } }"
              />
              <q-btn
                v-if="authStore.isAdmin"
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click="editHub(props.row)"
              />
              <q-btn
                v-if="authStore.isSuperAdmin"
                flat
                round
                dense
                icon="delete"
                color="negative"
                @click="deleteHub(props.row)"
              />
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Create/Edit Dialog -->
    <q-dialog v-model="showCreateDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">{{ editingHub ? 'Edit Hub' : 'Create Hub' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveHub" class="q-gutter-md">
            <q-input
              v-model="formData.name"
              label="Hub Name"
              outlined
              :rules="[val => !!val || 'Name is required']"
            />

            <q-input
              v-model="formData.location"
              label="Location"
              outlined
              :rules="[val => !!val || 'Location is required']"
            />

            <q-input
              v-model="formData.description"
              label="Description"
              type="textarea"
              outlined
              rows="3"
            />

            <div class="row justify-end q-gutter-sm">
              <q-btn
                label="Cancel"
                flat
                v-close-popup
              />
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
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const authStore = useAuthStore()

const hubs = ref([])
const loading = ref(false)
const filter = ref('')
const showCreateDialog = ref(false)
const editingHub = ref(null)
const saving = ref(false)

const formData = ref({
  name: '',
  location: '',
  description: ''
})

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true },
  { name: 'name', label: 'Name', field: 'name', align: 'left', sortable: true },
  { name: 'location', label: 'Location', field: 'location', align: 'left', sortable: true },
  { name: 'description', label: 'Description', field: 'description', align: 'left' },
  { name: 'actions', label: 'Actions', align: 'center' }
]

const loadHubs = async () => {
  loading.value = true
  try {
    const response = await hubsAPI.list()
    hubs.value = response.data
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load hubs',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const editHub = (hub) => {
  editingHub.value = hub
  formData.value = { ...hub }
  showCreateDialog.value = true
}

const saveHub = async () => {
  saving.value = true
  try {
    if (editingHub.value) {
      await hubsAPI.update(editingHub.value.id, formData.value)
      $q.notify({
        type: 'positive',
        message: 'Hub updated successfully',
        position: 'top'
      })
    } else {
      await hubsAPI.create(formData.value)
      $q.notify({
        type: 'positive',
        message: 'Hub created successfully',
        position: 'top'
      })
    }
    showCreateDialog.value = false
    resetForm()
    loadHubs()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to save hub',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

const deleteHub = (hub) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Are you sure you want to delete "${hub.name}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await hubsAPI.delete(hub.id)
      $q.notify({
        type: 'positive',
        message: 'Hub deleted successfully',
        position: 'top'
      })
      loadHubs()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: 'Failed to delete hub',
        position: 'top'
      })
    }
  })
}

const resetForm = () => {
  formData.value = {
    name: '',
    location: '',
    description: ''
  }
  editingHub.value = null
}

onMounted(() => {
  loadHubs()
})
</script>
