import { reactive } from 'vue'
import {
  getMutationQueue,
  removeMutation,
  updateMutation,
  getPendingMutationCount,
  invalidateCacheByPrefix,
  invalidateCacheByPattern,
  clearExpiredCache,
  getSyncMeta,
  setSyncMeta,
  addTempIdMapping,
  getTempIdMappings,
  clearTempIdMappings
} from './offlineDb'
import { useAuthStore } from 'stores/auth'

const MAX_RETRIES = 5
const SYNC_DEBOUNCE_MS = 2000
const PERIODIC_SYNC_MS = 30000
const CACHE_CLEANUP_MS = 10 * 60 * 1000
const SYNC_LOCK_TIMEOUT_MS = 60000

export const syncState = reactive({
  syncing: false,
  pendingCount: 0,
  lastSyncAt: null,
  lastError: null
})

let axiosInstance = null
let onlineDebounceTimer = null
let periodicSyncTimer = null
let cacheCleanupTimer = null

// Determine which cache keys to invalidate based on a mutation URL.
function getCacheInvalidationTargets (url) {
  const prefixes = []
  const patterns = []

  const path = url.replace(/^https?:\/\/[^/]+/, '')

  const match = path.match(/^\/([^/?]+)/)
  if (match) {
    const resource = match[1]
    prefixes.push(`GET:/${resource}/`)
    prefixes.push(`GET:/${resource}?`)
    prefixes.push(`GET:/${resource}`)
  }

  const nestedMatch = path.match(/^\/([^/]+)\/([^/]+)\/([^/]+)/)
  if (nestedMatch) {
    const parentResource = nestedMatch[1]
    const childResource = nestedMatch[3]
    prefixes.push(`GET:/${parentResource}/`)
    patterns.push(new RegExp(`^GET:/${parentResource}/[^/]+/${childResource}`))
  }

  if (/\/(battery-rentals|pue-rentals|rentals)/.test(path)) {
    prefixes.push('GET:/battery-rentals')
    prefixes.push('GET:/pue-rentals')
    prefixes.push('GET:/rentals/')
    prefixes.push('GET:/rentals?')
  }

  if (/\/users\//.test(path) || /^\/users\/?$/.test(path)) {
    prefixes.push('GET:/users/')
    prefixes.push('GET:/users?')
    patterns.push(/^GET:\/hubs\/[^/]+\/users/)
  }

  if (/\/accounts\//.test(path)) {
    prefixes.push('GET:/accounts/')
  }

  if (/\/batteries\//.test(path) || /^\/batteries\/?$/.test(path)) {
    prefixes.push('GET:/batteries/')
    prefixes.push('GET:/batteries?')
    patterns.push(/^GET:\/hubs\/[^/]+\/batteries/)
  }

  if (/\/pue\//.test(path) || /^\/pue\/?$/.test(path)) {
    prefixes.push('GET:/pue/')
    prefixes.push('GET:/pue?')
    patterns.push(/^GET:\/hubs\/[^/]+\/pue/)
  }

  return { prefixes, patterns }
}

// Extract the real ID from a server response after a create
function extractRealId (responseData) {
  if (!responseData || typeof responseData !== 'object') return null
  // Try common ID fields in order of specificity
  return responseData.user_id || responseData.battery_id || responseData.rental_id || responseData.pue_id || responseData.id || null
}

// Substitute temp IDs in a mutation's URL and data before sending
function substituteTempIds (mutation, mappings) {
  let { url, data } = mutation
  let changed = false

  // Substitute in URL path (handles negative IDs like /-1/ or /-1)
  for (const [tempId, realId] of Object.entries(mappings)) {
    const escaped = tempId.replace('-', '\\-')
    const urlPattern = new RegExp(`(/)${escaped}(/|$|\\?)`, 'g')
    const newUrl = url.replace(urlPattern, `$1${realId}$2`)
    if (newUrl !== url) {
      url = newUrl
      changed = true
    }
  }

  // Substitute in JSON data
  if (data && typeof data === 'object') {
    let jsonStr = JSON.stringify(data)
    for (const [tempId, realId] of Object.entries(mappings)) {
      // Match the temp ID as a number value in JSON (e.g. "user_id":-1)
      const numPattern = new RegExp(`:${tempId.replace('-', '\\-')}([,}\\]])`, 'g')
      const newJson = jsonStr.replace(numPattern, `:${realId}$1`)
      if (newJson !== jsonStr) {
        jsonStr = newJson
        changed = true
      }

      // Also match as string value (e.g. "battery_id":"-1")
      const strPattern = new RegExp(`"${tempId.replace('-', '\\-')}"`, 'g')
      const newJson2 = jsonStr.replace(strPattern, `"${realId}"`)
      if (newJson2 !== jsonStr) {
        jsonStr = newJson2
        changed = true
      }

      // Match in arrays (e.g. "battery_ids":[-1, 5])
      const arrPattern = new RegExp(`([\\[,])${tempId.replace('-', '\\-')}([,\\]])`, 'g')
      const newJson3 = jsonStr.replace(arrPattern, `$1${realId}$2`)
      if (newJson3 !== jsonStr) {
        jsonStr = newJson3
        changed = true
      }
    }
    if (changed) {
      try { data = JSON.parse(jsonStr) } catch { /* keep original */ }
    }
  }

  return { url, data, changed }
}

// Process the mutation queue sequentially (FIFO).
async function processQueue () {
  if (!axiosInstance) return

  const lockTime = await getSyncMeta('syncLockTime')
  if (lockTime && Date.now() - lockTime < SYNC_LOCK_TIMEOUT_MS) {
    return
  }

  await setSyncMeta('syncLockTime', Date.now())

  syncState.syncing = true
  syncState.lastError = null

  try {
    const queue = await getMutationQueue()
    syncState.pendingCount = queue.length

    if (queue.length === 0) {
      syncState.syncing = false
      return
    }

    const authStore = useAuthStore()

    for (const mutation of queue) {
      if (!navigator.onLine) break

      try {
        const headers = { ...mutation.headers }
        if (authStore.token) {
          headers.Authorization = `Bearer ${authStore.token}`
        }
        if (mutation.data && typeof mutation.data === 'object') {
          headers['Content-Type'] = 'application/json'
        }

        // Substitute any temp IDs with real IDs from previous syncs
        const mappings = await getTempIdMappings()
        const { url, data } = substituteTempIds(mutation, mappings)

        const response = await axiosInstance({
          method: mutation.method,
          url,
          data,
          headers,
          _bypassOffline: true
        })

        // If this mutation had a tempId, record the mapping to the real ID
        if (mutation.tempId && response.data) {
          const realId = extractRealId(response.data)
          if (realId) {
            await addTempIdMapping(String(mutation.tempId), realId)
          }
        }

        // Success - remove from queue and invalidate related cache
        await removeMutation(mutation.id)
        syncState.pendingCount--

        const { prefixes, patterns } = getCacheInvalidationTargets(url)
        for (const prefix of prefixes) {
          await invalidateCacheByPrefix(prefix)
        }
        for (const pattern of patterns) {
          await invalidateCacheByPattern(pattern)
        }
      } catch (error) {
        if (error.response?.status === 401) {
          syncState.lastError = 'Session expired. Please log in again.'
          break
        }

        if (error.response && error.response.status >= 400 && error.response.status < 500) {
          await updateMutation(mutation.id, { status: 'failed' })
          syncState.pendingCount--
          continue
        }

        const newRetryCount = (mutation.retryCount || 0) + 1
        if (newRetryCount >= MAX_RETRIES) {
          await updateMutation(mutation.id, { status: 'failed', retryCount: newRetryCount })
          syncState.pendingCount--
          continue
        }

        await updateMutation(mutation.id, { retryCount: newRetryCount })
        syncState.lastError = 'Some changes failed to sync. Will retry.'
        break
      }
    }

    syncState.lastSyncAt = Date.now()
  } finally {
    syncState.syncing = false
    await setSyncMeta('syncLockTime', null)
    syncState.pendingCount = await getPendingMutationCount()

    // Clear temp ID mappings if queue is empty (all synced)
    if (syncState.pendingCount === 0) {
      await clearTempIdMappings()
    }
  }
}

export function triggerSync () {
  if (onlineDebounceTimer) {
    clearTimeout(onlineDebounceTimer)
  }
  onlineDebounceTimer = setTimeout(() => {
    if (navigator.onLine && !syncState.syncing) {
      processQueue()
    }
  }, SYNC_DEBOUNCE_MS)
}

export function getSyncState () {
  return syncState
}

export async function initSyncManager (axios) {
  axiosInstance = axios

  syncState.pendingCount = await getPendingMutationCount()

  window.addEventListener('online', () => {
    triggerSync()
  })

  periodicSyncTimer = setInterval(() => {
    if (navigator.onLine && !syncState.syncing && syncState.pendingCount > 0) {
      processQueue()
    }
  }, PERIODIC_SYNC_MS)

  cacheCleanupTimer = setInterval(() => {
    clearExpiredCache().catch(() => {})
  }, CACHE_CLEANUP_MS)

  if (navigator.onLine && syncState.pendingCount > 0) {
    triggerSync()
  }
}
