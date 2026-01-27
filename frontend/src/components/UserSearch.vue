<template>
  <div class="user-search">
    <q-select
      v-model="selectedUser"
      :options="filteredUsers"
      option-label="username"
      option-value="id"
      use-input
      input-debounce="300"
      label="Search Customer"
      outlined
      clearable
      @filter="filterUsers"
      @update:model-value="handleUserSelect"
    >
      <template v-slot:prepend>
        <q-icon name="search" />
      </template>

      <template v-slot:option="scope">
        <q-item v-bind="scope.itemProps">
          <q-item-section avatar>
            <q-avatar color="primary" text-color="white">
              {{ scope.opt.username.charAt(0).toUpperCase() }}
            </q-avatar>
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ scope.opt.full_name || scope.opt.username }}</q-item-label>
            <q-item-label caption>
              ID: {{ scope.opt.short_id || `BH-${String(scope.opt.id).padStart(4, '0')}` }}
            </q-item-label>
            <q-item-label caption v-if="scope.opt.email">
              {{ scope.opt.email }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>

      <template v-slot:no-option>
        <q-item>
          <q-item-section class="text-grey">
            No customers found
          </q-item-section>
        </q-item>
      </template>
    </q-select>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  users: {
    type: Array,
    required: true
  },
  modelValue: {
    type: [Object, Number],
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

const selectedUser = ref(props.modelValue)
const filterText = ref('')

const filteredUsers = computed(() => {
  if (!filterText.value) {
    return props.users
  }

  const search = filterText.value.toLowerCase()
  return props.users.filter(user => {
    const shortId = user.short_id || `BH-${String(user.id).padStart(4, '0')}`
    return (
      user.username?.toLowerCase().includes(search) ||
      user.full_name?.toLowerCase().includes(search) ||
      user.email?.toLowerCase().includes(search) ||
      shortId.toLowerCase().includes(search)
    )
  })
})

const filterUsers = (val, update) => {
  update(() => {
    filterText.value = val
  })
}

const handleUserSelect = (user) => {
  emit('update:modelValue', user)
  emit('select', user)
}
</script>

<style scoped>
.user-search {
  width: 100%;
}
</style>
