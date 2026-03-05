import { boot } from 'quasar/wrappers'
import { ref } from 'vue'
import { openDb } from 'src/services/offlineDb'
import { installOfflineInterceptors } from 'src/services/offlineInterceptor'
import { initSyncManager, syncState } from 'src/services/syncManager'
import { warmCache } from 'src/services/cacheWarmer'
import { useAuthStore } from 'stores/auth'
import api from 'src/services/api'

export default boot(async ({ app }) => {
  // Open IndexedDB (creates stores on first run)
  // Wrapped in try-catch so app still works if IndexedDB is unavailable
  // (e.g. private browsing in older Safari, or storage quota exceeded)
  try {
    await openDb()
  } catch (err) {
    console.warn('IndexedDB unavailable — offline features disabled:', err.message)
  }

  // Install offline interceptors on the shared axios instance
  installOfflineInterceptors(api)

  // Initialize sync manager (sets up online/offline listeners, periodic sync)
  await initSyncManager(api)

  // Reactive network state
  const networkOnline = ref(navigator.onLine)

  window.addEventListener('online', async () => {
    networkOnline.value = true
    const authStore = useAuthStore()
    // Refresh token on reconnect so users don't get locked out
    if (authStore.isAuthenticated) {
      await authStore.refreshToken()
    }
    // Re-warm cache when connectivity returns
    warmCache(api, authStore)
  })
  window.addEventListener('offline', () => {
    networkOnline.value = false
  })

  // Provide to all components via inject()
  app.provide('networkState', { online: networkOnline })
  app.provide('offlineSyncState', syncState)

  // Warm cache on startup if already authenticated and online
  if (navigator.onLine) {
    const authStore = useAuthStore()
    if (authStore.isAuthenticated) {
      // Fire-and-forget: don't block app startup
      warmCache(api, authStore)
    }
  }

  // Expose manual trigger for dev/testing: run warmCacheNow() in browser console
  window.warmCacheNow = () => {
    const authStore = useAuthStore()
    return warmCache(api, authStore, { force: true })
  }
})
