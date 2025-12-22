<template>
  <router-view />
</template>

<script>
import { defineComponent, onMounted } from 'vue'
import { useHubSettingsStore } from 'stores/hubSettings'
import { useAuthStore } from 'stores/auth'

export default defineComponent({
  name: 'App',
  setup() {
    const hubSettingsStore = useHubSettingsStore()
    const authStore = useAuthStore()

    // Initialize hub settings when app loads
    onMounted(async () => {
      if (authStore.isAuthenticated) {
        await hubSettingsStore.initialize()
      }
    })
  }
})
</script>
