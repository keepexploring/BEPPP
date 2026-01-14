<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="col-12 col-sm">
        <q-btn
          flat
          round
          dense
          icon="arrow_back"
          @click="$router.back()"
        />
        <span class="text-h5 q-ml-md">{{ hub?.what_three_word_location || `Hub #${hub?.hub_id}` || 'Hub Details' }}</span>
      </div>
      <div class="col-12 col-sm-auto">
        <q-btn
          v-if="authStore.isAdmin"
          color="primary"
          label="Edit Hub"
          icon="edit"
          @click="openEditDialog"
          size="sm"
          class="col-12 col-sm-auto"
        />
      </div>
    </div>

    <div v-if="loading" class="flex flex-center q-pa-xl">
      <q-spinner-gears size="50px" color="primary" />
    </div>

    <div v-else-if="hub" class="row q-col-gutter-md">
      <!-- Hub Info Card -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Hub Information</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div class="q-gutter-sm">
              <div><strong>Hub ID:</strong> {{ hub.hub_id }}</div>
              <div><strong>Location:</strong> {{ hub.what_three_word_location }}</div>
              <div><strong>Country:</strong> {{ hub.country }}</div>
              <div v-if="hub.solar_capacity_kw">
                <strong>Solar Capacity:</strong> {{ hub.solar_capacity_kw }} kW
              </div>
              <div v-if="hub.latitude && hub.longitude">
                <strong>Coordinates:</strong> {{ hub.latitude.toFixed(6) }}, {{ hub.longitude.toFixed(6) }}
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Statistics Card -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Statistics</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div class="q-gutter-sm">
              <div class="row items-center">
                <div class="col">
                  <q-icon name="battery_charging_full" size="sm" color="primary" />
                  <span class="q-ml-sm">Batteries:</span>
                </div>
                <div class="col-auto text-h6">{{ batteries.length }}</div>
              </div>
              <div class="row items-center">
                <div class="col">
                  <q-icon name="devices" size="sm" color="accent" />
                  <span class="q-ml-sm">Equipment:</span>
                </div>
                <div class="col-auto text-h6">{{ pueItems.length }}</div>
              </div>
              <div class="row items-center">
                <div class="col">
                  <q-icon name="people" size="sm" color="secondary" />
                  <span class="q-ml-sm">Users:</span>
                </div>
                <div class="col-auto text-h6">{{ users.length }}</div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Batteries -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Batteries</div>
              </div>
              <div class="col-auto">
                <q-btn
                  v-if="authStore.isAdmin"
                  label="Add Battery"
                  icon="add"
                  color="primary"
                  size="sm"
                  :to="{ name: 'batteries' }"
                />
              </div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list v-if="batteries.length > 0" separator>
              <q-item
                v-for="battery in batteries"
                :key="battery.battery_id"
                clickable
                :to="{ name: 'battery-detail', params: { id: battery.battery_id } }"
              >
                <q-item-section avatar>
                  <q-icon name="battery_charging_full" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Battery #{{ battery.battery_id }}{{ battery.short_id ? ` (${battery.short_id})` : '' }}</q-item-label>
                  <q-item-label caption>
                    {{ battery.battery_capacity_wh || '-' }} Wh
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge :color="getStatusColor(battery.status)">
                    {{ battery.status }}
                  </q-badge>
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No batteries available
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- PUE Equipment -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">Equipment (PUE)</div>
              </div>
              <div class="col-auto">
                <q-btn
                  v-if="authStore.isAdmin"
                  label="Add Equipment"
                  icon="add"
                  color="primary"
                  size="sm"
                  :to="{ name: 'pue' }"
                />
              </div>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list v-if="pueItems.length > 0" separator>
              <q-item v-for="pue in pueItems" :key="pue.pue_id" clickable :to="{ name: 'pue' }">
                <q-item-section avatar>
                  <q-icon name="devices" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ pue.name }}{{ pue.power_rating_watts ? ` (${pue.power_rating_watts}W)` : '' }}</q-item-label>
                  <q-item-label caption>{{ pue.description || 'No description' }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div v-if="pue.suggested_cost_per_day || pue.rental_cost" class="text-caption">
                    {{ currencySymbol }}{{ pue.rental_cost || pue.suggested_cost_per_day }}/day
                  </div>
                  <q-badge :color="getStatusColor(pue.status)">
                    {{ pue.status }}
                  </q-badge>
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No equipment available
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Users -->
      <div class="col-12" v-if="authStore.isAdmin">
        <q-card>
          <q-card-section>
            <div class="text-h6">Authorized Users</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list v-if="users.length > 0" separator>
              <q-item v-for="user in users" :key="user.user_id" clickable :to="{ name: 'user-detail', params: { id: user.user_id } }">
                <q-item-section avatar>
                  <q-icon name="person" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ user.Name || user.username || `User ${user.user_id}` }}</q-item-label>
                  <q-item-label caption>{{ user.username }}{{ user.mobile_number ? ` • ${user.mobile_number}` : '' }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge :color="getRoleColor(user.user_access_level)">{{ user.user_access_level }}</q-badge>
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No users authorized for this hub
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Edit Hub Dialog -->
    <q-dialog v-model="showEditDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Edit Hub</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveHub" class="q-gutter-md">
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

            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input
                  v-model.number="formData.latitude"
                  label="Latitude"
                  type="number"
                  step="any"
                  outlined
                />
              </div>
              <div class="col-6">
                <q-input
                  v-model.number="formData.longitude"
                  label="Longitude"
                  type="number"
                  step="any"
                  outlined
                />
              </div>
            </div>

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
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const route = useRoute()
const authStore = useAuthStore()
const hubSettingsStore = useHubSettingsStore()

const currencySymbol = computed(() => hubSettingsStore.currentCurrencySymbol)

const hub = ref(null)
const batteries = ref([])
const pueItems = ref([])
const users = ref([])
const loading = ref(true)
const showEditDialog = ref(false)
const saving = ref(false)

const formData = ref({
  hub_id: null,
  what_three_word_location: '',
  solar_capacity_kw: null,
  country: '',
  latitude: null,
  longitude: null
})

const getStatusColor = (status) => {
  const colors = {
    available: 'positive',
    rented: 'warning',
    maintenance: 'info',
    retired: 'negative'
  }
  return colors[status] || 'grey'
}

const getRoleColor = (role) => {
  const colors = {
    user: 'grey',
    admin: 'primary',
    superadmin: 'purple',
    data_admin: 'info'
  }
  return colors[role] || 'grey'
}

const loadHubDetails = async () => {
  loading.value = true

  try {
    const hubId = route.params.id

    // Load hub info
    const hubResponse = await hubsAPI.get(hubId)
    hub.value = hubResponse.data

    // Load batteries
    const batteriesResponse = await hubsAPI.getBatteries(hubId)
    batteries.value = batteriesResponse.data

    // Load PUE
    const pueResponse = await hubsAPI.getPUE(hubId)
    pueItems.value = pueResponse.data

    // Load users (if admin)
    if (authStore.isAdmin) {
      const usersResponse = await hubsAPI.getUsers(hubId)
      users.value = usersResponse.data
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load hub details',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const openEditDialog = () => {
  formData.value = { ...hub.value }
  showEditDialog.value = true
}

const saveHub = async () => {
  saving.value = true
  try {
    await hubsAPI.update(hub.value.hub_id, formData.value)
    $q.notify({
      type: 'positive',
      message: 'Hub updated successfully',
      position: 'top'
    })
    showEditDialog.value = false
    await loadHubDetails()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to update hub',
      position: 'top'
    })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadHubDetails()
})
</script>
