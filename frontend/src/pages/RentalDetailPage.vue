<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <q-btn flat round dense icon="arrow_back" @click="$router.back()" />
        <span class="text-h4 q-ml-md">Rental #{{ $route.params.id }}</span>
      </div>
    </div>

    <div v-if="loading" class="flex flex-center q-pa-xl">
      <q-spinner-gears size="50px" color="primary" />
    </div>

    <div v-else-if="rental" class="row q-col-gutter-md">
      <div class="col-12">
        <q-banner v-if="rental.status === 'overdue'" class="bg-negative text-white">
          <template v-slot:avatar>
            <q-icon name="warning" />
          </template>
          This rental is overdue!
        </q-banner>
      </div>

      <!-- Rental Info -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Rental Information</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <div><strong>ID:</strong> {{ rental.id }}</div>
            <div><strong>User:</strong> {{ rental.user?.username || rental.user_id }}</div>
            <div><strong>Battery:</strong> {{ rental.battery?.serial_number || rental.battery_id }}</div>
            <div>
              <strong>Status:</strong>
              <q-badge :color="getStatusColor(rental.status)" class="q-ml-sm">
                {{ rental.status }}
              </q-badge>
            </div>
            <div><strong>Rental Date:</strong> {{ formatDate(rental.rental_date) }}</div>
            <div><strong>Expected Return:</strong> {{ formatDate(rental.expected_return_date) }}</div>
            <div v-if="rental.actual_return_date">
              <strong>Actual Return:</strong> {{ formatDate(rental.actual_return_date) }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Costs -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Cost Breakdown</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-gutter-sm">
            <div><strong>Daily Rate:</strong> ${{ rental.daily_rate }}</div>
            <div><strong>Deposit:</strong> ${{ rental.deposit_amount }}</div>
            <div><strong>Days Rented:</strong> {{ calculateDays(rental) }}</div>
            <div class="text-h6 text-primary q-mt-md">
              <strong>Total Cost:</strong> ${{ rental.total_cost?.toFixed(2) || '0.00' }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- PUE Items -->
      <div class="col-12" v-if="rental.pue_items && rental.pue_items.length > 0">
        <q-card>
          <q-card-section>
            <div class="text-h6">Equipment (PUE) Items</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-list separator>
              <q-item v-for="item in rental.pue_items" :key="item.id">
                <q-item-section avatar>
                  <q-icon name="devices" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ item.pue?.name || `PUE #${item.pue_id}` }}</q-item-label>
                  <q-item-label caption>
                    Rented: {{ formatDate(item.rental_date) }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge v-if="item.return_date" color="grey">
                    Returned: {{ formatDate(item.return_date) }}
                  </q-badge>
                  <q-badge v-else color="positive">Active</q-badge>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <!-- Notes -->
      <div class="col-12" v-if="rental.return_notes">
        <q-card>
          <q-card-section>
            <div class="text-h6">Return Notes</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            {{ rental.return_notes }}
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { rentalsAPI } from 'src/services/api'
import { useQuasar, date } from 'quasar'

const $q = useQuasar()
const route = useRoute()

const rental = ref(null)
const loading = ref(true)

const getStatusColor = (status) => {
  const colors = {
    active: 'positive',
    returned: 'grey',
    overdue: 'negative',
    cancelled: 'warning'
  }
  return colors[status] || 'grey'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return date.formatDate(dateStr, 'MMM DD, YYYY HH:mm')
}

const calculateDays = (rental) => {
  if (!rental.rental_date || !rental.expected_return_date) return 0

  const start = new Date(rental.rental_date)
  const end = rental.actual_return_date
    ? new Date(rental.actual_return_date)
    : new Date(rental.expected_return_date)

  return Math.ceil((end - start) / (1000 * 60 * 60 * 24))
}

const loadRentalDetails = async () => {
  loading.value = true

  try {
    const rentalId = route.params.id
    const response = await rentalsAPI.get(rentalId)
    rental.value = response.data
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load rental details',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRentalDetails()
})
</script>
