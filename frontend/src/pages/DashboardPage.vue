<template>
  <q-page class="q-pa-md">
    <div class="text-h4 q-mb-md">Dashboard</div>

    <div class="row q-col-gutter-md">
      <!-- Summary Cards -->
      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Total Hubs</div>
                <div class="text-h4">{{ stats.totalHubs }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="hub" size="48px" color="primary" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Active Batteries</div>
                <div class="text-h4">{{ stats.activeBatteries }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="battery_charging_full" size="48px" color="positive" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Active Rentals</div>
                <div class="text-h4">{{ stats.activeRentals }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="receipt" size="48px" color="accent" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="stat-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-overline text-grey-7">Total Revenue</div>
                <div class="text-h4">${{ stats.totalRevenue }}</div>
              </div>
              <div class="col-auto">
                <q-icon name="attach_money" size="48px" color="warning" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Hub Summary -->
      <div class="col-12 col-md-8">
        <q-card>
          <q-card-section>
            <div class="text-h6">Hub Summary</div>
          </q-card-section>
          <q-card-section>
            <q-list v-if="hubSummary.length > 0" separator>
              <q-item v-for="hub in hubSummary" :key="hub.hub_id">
                <q-item-section>
                  <q-item-label>{{ hub.hub_name }}</q-item-label>
                  <q-item-label caption>
                    {{ hub.total_batteries }} batteries, {{ hub.active_batteries }} active
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn
                    flat
                    round
                    dense
                    icon="arrow_forward"
                    :to="{ name: 'hub-detail', params: { id: hub.hub_id } }"
                  />
                </q-item-section>
              </q-item>
            </q-list>
            <div v-else class="text-center text-grey-7 q-pa-md">
              No hubs available
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Recent Activity -->
      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">Quick Actions</div>
          </q-card-section>
          <q-card-section class="q-gutter-sm">
            <q-btn
              label="New Rental"
              icon="add"
              color="primary"
              class="full-width"
              :to="{ name: 'rentals' }"
            />
            <q-btn
              label="Add Battery"
              icon="battery_plus"
              color="positive"
              outline
              class="full-width"
              :to="{ name: 'batteries' }"
            />
            <q-btn
              label="View Analytics"
              icon="analytics"
              color="accent"
              outline
              class="full-width"
              :to="{ name: 'analytics' }"
            />
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { hubsAPI, analyticsAPI } from 'src/services/api'
import { useQuasar } from 'quasar'

const $q = useQuasar()

const stats = ref({
  totalHubs: 0,
  activeBatteries: 0,
  activeRentals: 0,
  totalRevenue: 0
})

const hubSummary = ref([])

const loadDashboardData = async () => {
  $q.loading.show()

  try {
    // Load hub summary
    const hubsResponse = await analyticsAPI.hubSummary()
    hubSummary.value = hubsResponse.data

    // Calculate stats
    stats.value.totalHubs = hubSummary.value.length
    stats.value.activeBatteries = hubSummary.value.reduce(
      (sum, hub) => sum + (hub.active_batteries || 0),
      0
    )

    // Load revenue data
    try {
      const revenueResponse = await analyticsAPI.revenue({
        time_period: 'last_month'
      })
      if (revenueResponse.data?.total_revenue) {
        stats.value.totalRevenue = revenueResponse.data.total_revenue.toFixed(2)
      }
    } catch (error) {
      console.error('Error loading revenue:', error)
    }

  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load dashboard data',
      position: 'top'
    })
  } finally {
    $q.loading.hide()
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.stat-card {
  height: 100%;
}
</style>
