<template>
  <q-dialog v-model="show" position="top" @hide="onHide">
    <q-card style="width: 100%; max-width: 600px; margin-top: 60px">
      <q-card-section class="q-pb-none">
        <q-input
          ref="inputRef"
          v-model="query"
          placeholder="Search users, batteries, rentals..."
          outlined
          autofocus
          clearable
          debounce="300"
          @update:model-value="doSearch"
          @keydown.esc="show = false"
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
          <template v-slot:append>
            <q-spinner v-if="loading" color="primary" size="sm" />
          </template>
        </q-input>
      </q-card-section>

      <!-- No query state -->
      <q-card-section v-if="!query" class="text-center text-grey-6 q-py-lg">
        Type to search across users, batteries, and rentals
      </q-card-section>

      <!-- No results -->
      <q-card-section v-else-if="!loading && hasNoResults" class="text-center text-grey-6 q-py-lg">
        No results found for "{{ query }}"
      </q-card-section>

      <!-- Results -->
      <q-list v-else-if="!loading && !hasNoResults" separator>

        <!-- Users -->
        <template v-if="results.users.length">
          <q-item-label header class="text-weight-bold q-pt-md q-pb-xs">
            <q-icon name="person" size="xs" class="q-mr-xs" /> Users ({{ results.users.length }})
          </q-item-label>
          <q-item
            v-for="item in results.users"
            :key="`u-${item.id}`"
            clickable
            v-ripple
            @click="navigate(item.route)"
          >
            <q-item-section avatar>
              <q-avatar color="primary" text-color="white" size="sm" icon="person" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption>{{ item.caption }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-chip v-if="item.short_id" dense size="sm" color="grey-3">{{ item.short_id }}</q-chip>
            </q-item-section>
          </q-item>
        </template>

        <!-- Batteries -->
        <template v-if="results.batteries.length">
          <q-item-label header class="text-weight-bold q-pt-md q-pb-xs">
            <q-icon name="battery_charging_full" size="xs" class="q-mr-xs" /> Batteries ({{ results.batteries.length }})
          </q-item-label>
          <q-item
            v-for="item in results.batteries"
            :key="`b-${item.id}`"
            clickable
            v-ripple
            @click="navigate(item.route)"
          >
            <q-item-section avatar>
              <q-avatar :color="statusColor(item.status)" text-color="white" size="sm" icon="battery_full" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption>{{ item.caption }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-chip dense size="sm" :color="statusColor(item.status)" text-color="white">{{ item.status }}</q-chip>
            </q-item-section>
          </q-item>
        </template>

        <!-- Battery Rentals -->
        <template v-if="results.battery_rentals.length">
          <q-item-label header class="text-weight-bold q-pt-md q-pb-xs">
            <q-icon name="receipt" size="xs" class="q-mr-xs" /> Battery Rentals ({{ results.battery_rentals.length }})
          </q-item-label>
          <q-item
            v-for="item in results.battery_rentals"
            :key="`br-${item.id}`"
            clickable
            v-ripple
            @click="navigate(item.route)"
          >
            <q-item-section avatar>
              <q-avatar :color="item.status === 'active' ? 'positive' : 'grey'" text-color="white" size="sm" icon="receipt" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption>{{ item.caption }}</q-item-label>
            </q-item-section>
          </q-item>
        </template>

        <!-- PUE Rentals -->
        <template v-if="results.pue_rentals.length">
          <q-item-label header class="text-weight-bold q-pt-md q-pb-xs">
            <q-icon name="devices" size="xs" class="q-mr-xs" /> PUE Rentals ({{ results.pue_rentals.length }})
          </q-item-label>
          <q-item
            v-for="item in results.pue_rentals"
            :key="`pr-${item.id}`"
            clickable
            v-ripple
            @click="navigate(item.route)"
          >
            <q-item-section avatar>
              <q-avatar :color="item.active ? 'positive' : 'grey'" text-color="white" size="sm" icon="devices" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption>{{ item.caption }}</q-item-label>
            </q-item-section>
          </q-item>
        </template>

      </q-list>

      <div class="q-py-xs" />
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { searchAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const router = useRouter()
const authStore = useAuthStore()

const show = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const query = ref('')
const loading = ref(false)
const results = ref({ users: [], batteries: [], battery_rentals: [], pue_rentals: [] })

const hasNoResults = computed(() =>
  results.value.users.length === 0 &&
  results.value.batteries.length === 0 &&
  results.value.battery_rentals.length === 0 &&
  results.value.pue_rentals.length === 0
)

const doSearch = async (q) => {
  if (!q || q.length < 2) {
    results.value = { users: [], batteries: [], battery_rentals: [], pue_rentals: [] }
    return
  }
  loading.value = true
  try {
    const hubId = authStore.currentHubId || undefined
    const res = await searchAPI.search(q, hubId)
    results.value = res.data.results
  } catch {
    results.value = { users: [], batteries: [], battery_rentals: [], pue_rentals: [] }
  } finally {
    loading.value = false
  }
}

const navigate = (route) => {
  show.value = false
  router.push(route)
}

const onHide = () => {
  query.value = ''
  results.value = { users: [], batteries: [], battery_rentals: [], pue_rentals: [] }
}

const statusColor = (status) => {
  if (status === 'available') return 'positive'
  if (status === 'rented') return 'warning'
  if (status === 'maintenance') return 'orange'
  return 'grey'
}
</script>
