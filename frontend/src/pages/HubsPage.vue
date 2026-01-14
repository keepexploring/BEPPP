<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="col-12 col-sm-auto">
        <div class="text-h5">Hubs</div>
      </div>
      <div class="col-12 col-sm row justify-end">
        <q-btn
          v-if="authStore.isAdmin"
          label="Add Hub"
          icon="add"
          color="primary"
          @click="showCreateDialog = true"
          size="sm"
          class="col-12 col-sm-auto"
        />
      </div>
    </div>

    <q-card>
      <q-card-section>
        <q-table
          :rows="hubs"
          :columns="columns"
          row-key="hub_id"
          :loading="loading"
          :filter="filter"
          @row-click="(_evt, row) => $router.push({ name: 'hub-detail', params: { id: row.hub_id } })"
          class="cursor-pointer"
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
                :to="{ name: 'hub-detail', params: { id: props.row.hub_id } }"
              />
              <q-btn
                v-if="authStore.isAdmin"
                flat
                round
                dense
                icon="edit"
                color="warning"
                @click.stop="editHub(props.row)"
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
              v-if="!editingHub"
              v-model.number="formData.hub_id"
              label="Hub ID"
              type="number"
              outlined
              :rules="[val => !!val || 'Hub ID is required']"
              hint="Unique identifier for this hub"
            />

            <q-input
              v-model="formData.what_three_word_location"
              label="What3Words Location"
              outlined
              :rules="[val => !!val || 'Location is required']"
              hint="e.g., main.solar.hub"
            />

            <q-input
              v-model.number="formData.solar_capacity_kw"
              label="Solar Capacity (kW)"
              type="number"
              outlined
              hint="Solar panel capacity in kilowatts"
            />

            <q-input
              v-model="formData.country"
              label="Country"
              outlined
            />

            <q-input
              v-model.number="formData.latitude"
              label="Latitude"
              type="number"
              step="any"
              outlined
              hint="Optional"
            />

            <q-input
              v-model.number="formData.longitude"
              label="Longitude"
              type="number"
              step="any"
              outlined
              hint="Optional"
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
  hub_id: null,
  what_three_word_location: '',
  solar_capacity_kw: null,
  country: '',
  latitude: null,
  longitude: null
})

const columns = [
  { name: 'hub_id', label: 'ID', field: 'hub_id', align: 'left', sortable: true },
  { name: 'what_three_word_location', label: 'Location', field: 'what_three_word_location', align: 'left', sortable: true },
  { name: 'country', label: 'Country', field: 'country', align: 'left', sortable: true },
  { name: 'solar_capacity_kw', label: 'Capacity (kW)', field: 'solar_capacity_kw', align: 'left', sortable: true },
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
      await hubsAPI.update(editingHub.value.hub_id, formData.value)
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
    message: `Are you sure you want to delete hub at "${hub.what_three_word_location}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await hubsAPI.delete(hub.hub_id)
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
    hub_id: null,
    what_three_word_location: '',
    solar_capacity_kw: null,
    country: '',
    latitude: null,
    longitude: null
  }
  editingHub.value = null
}

onMounted(() => {
  loadHubs()
})
</script>
