<template>
  <q-select
    v-model="selectedHub"
    :options="hubOptions"
    option-value="hub_id"
    option-label="label"
    emit-value
    map-options
    outlined
    dense
    label="Hub Filter"
    clearable
    :disable="loading"
    @update:model-value="handleHubChange"
    class="hub-filter-select"
    style="min-width: 200px"
  >
    <template v-slot:prepend>
      <q-icon name="hub" />
    </template>
  </q-select>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { hubsAPI } from 'src/services/api'
import { useAuthStore } from 'stores/auth'

const props = defineProps({
  modelValue: {
    type: [Number, String, null],
    default: null
  },
  showAllOption: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const authStore = useAuthStore()
const hubs = ref([])
const loading = ref(false)
const selectedHub = ref(props.modelValue)

const hubOptions = computed(() => {
  const options = []

  // Add "All Hubs" option if user is superadmin and showAllOption is true
  if (authStore.isSuperAdmin && props.showAllOption) {
    options.push({
      hub_id: null,
      label: 'All Hubs'
    })
  }

  // Add individual hubs
  hubs.value.forEach(hub => {
    options.push({
      hub_id: hub.hub_id,
      label: hub.what_three_word_location || `Hub ${hub.hub_id}`
    })
  })

  return options
})

const loadHubs = async () => {
  loading.value = true
  try {
    const response = await hubsAPI.list()
    hubs.value = response.data

    // If user is not a superadmin and has a hub_id, auto-select their hub
    if (!authStore.isSuperAdmin && authStore.user?.hub_id) {
      selectedHub.value = authStore.user.hub_id
      emit('update:modelValue', authStore.user.hub_id)
      emit('change', authStore.user.hub_id)
    } else if (!selectedHub.value && props.showAllOption && authStore.isSuperAdmin) {
      // Default to "All Hubs" for superadmins
      selectedHub.value = null
      emit('update:modelValue', null)
      emit('change', null)
    }
  } catch (error) {
    console.error('Failed to load hubs:', error)
  } finally {
    loading.value = false
  }
}

const handleHubChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// Watch for external changes to modelValue
watch(() => props.modelValue, (newVal) => {
  selectedHub.value = newVal
})

onMounted(() => {
  loadHubs()
})
</script>

<style scoped>
.hub-filter-select {
  background: white;
}
</style>
