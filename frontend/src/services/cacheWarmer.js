import { getSyncMeta, setSyncMeta } from './offlineDb'

const CONCURRENCY = 3
const WARM_COOLDOWN_MS = 5 * 60 * 1000 // Don't re-warm within 5 minutes

// Run an array of async functions with limited concurrency
async function runWithConcurrency (tasks, limit) {
  const results = []
  const executing = new Set()

  for (const task of tasks) {
    const p = task().then(
      (val) => { executing.delete(p); return val },
      () => { executing.delete(p) }
    )
    executing.add(p)
    results.push(p)

    if (executing.size >= limit) {
      await Promise.race(executing)
    }
  }

  await Promise.allSettled(results)
}

// Build the list of endpoints to prefetch for a given hub
export function getEndpointsForHub (hubId, isAdmin) {
  const endpoints = [
    // Hub-level data
    '/hubs/',
    `/hubs/${hubId}`,
    `/hubs/${hubId}/batteries`,
    `/hubs/${hubId}/users`,
    `/hubs/${hubId}/pue`,
    `/hubs/${hubId}/pue/available`,

    // Main list endpoints
    '/batteries/',
    `/batteries/?hub_id=${hubId}&status=available`,
    '/battery-rentals',
    '/pue-rentals',
    '/rentals/',
    '/rentals/overdue-upcoming',

    // Notifications
    `/notifications?hub_id=${hubId}`,

    // Settings (used across many pages)
    `/settings/rental-durations?hub_id=${hubId}`,
    `/settings/pue-types?hub_id=${hubId}`,
    '/settings/pricing',
    `/settings/payment-types?hub_id=${hubId}`,
    `/settings/payment-types?hub_id=${hubId}&is_active=true`,
    `/settings/hub/${hubId}`,
    `/settings/deposit-presets?hub_id=${hubId}`,
    `/settings/cost-structures?hub_id=${hubId}`,
    `/settings/subscription-packages?hub_id=${hubId}`,
    `/settings/customer-field-options?hub_id=${hubId}`,
    `/settings/return-survey-questions?hub_id=${hubId}`,

    // Survey (cache rental_type variants for offline return flow)
    `/return-survey/questions?rental_type=battery&hub_id=${hubId}`,
    `/return-survey/questions?rental_type=pue&hub_id=${hubId}`,

    // Accounts
    `/accounts/hub/${hubId}/summary`,
    '/accounts/users/in-debt',
  ]

  if (isAdmin) {
    endpoints.push(
      '/job-cards/',
      '/job-cards/admin-users',
      '/admin/webhook-logs'
    )
  }

  return endpoints
}

// Fetch detail pages for items from a list response
function getDetailEndpoints (listData, resourcePath, idField) {
  if (!Array.isArray(listData)) return []
  return listData
    .slice(0, 50) // Cap at 50 to avoid hammering the server
    .map((item) => `${resourcePath}/${item[idField]}`)
    .filter(Boolean)
}

/**
 * Warm the cache by pre-fetching all key API endpoints.
 * Runs in the background, never throws, never blocks UI.
 */
export async function warmCache (api, authStore, { force = false } = {}) {
  if (!navigator.onLine) {
    console.log('[CacheWarmer] Skipped: offline')
    return
  }
  if (!authStore.isAuthenticated) {
    console.log('[CacheWarmer] Skipped: not authenticated')
    return
  }

  const hubId = authStore.currentHubId
  if (!hubId) {
    console.log('[CacheWarmer] Skipped: no hub_id')
    return
  }

  // Cooldown check: don't re-warm too frequently (bypass with force)
  if (!force) {
    const lastWarm = await getSyncMeta('lastCacheWarm')
    if (lastWarm && Date.now() - lastWarm < WARM_COOLDOWN_MS) {
      console.log('[CacheWarmer] Skipped: cooldown active (last warm ' +
        Math.round((Date.now() - lastWarm) / 1000) + 's ago)')
      return
    }
  }

  console.log(`[CacheWarmer] Starting cache warm for hub ${hubId}` +
    (force ? ' (forced)' : ''))
  const startTime = Date.now()

  await setSyncMeta('lastCacheWarm', Date.now())

  const isAdmin = authStore.isAdmin

  // Phase 1: Fetch all list and settings endpoints
  const listEndpoints = getEndpointsForHub(hubId, isAdmin)
  const listTasks = listEndpoints.map((url) => () =>
    api.get(url).catch(() => null)
  )

  await runWithConcurrency(listTasks, CONCURRENCY)
  console.log(`[CacheWarmer] Phase 1 done: ${listEndpoints.length} list endpoints`)

  // Phase 2: Fetch individual detail pages from list results
  // We re-read the cached list data to extract IDs
  const detailTasks = []
  let batteriesRes, usersRes, pueRes, batteryRentalsRes, pueRentalsRes, jobCardsRes

  try {
    ;[batteriesRes, usersRes, pueRes, batteryRentalsRes, pueRentalsRes, jobCardsRes] = await Promise.allSettled([
      api.get('/batteries/'),
      api.get(`/hubs/${hubId}/users`),
      api.get(`/hubs/${hubId}/pue`),
      api.get('/battery-rentals'),
      api.get('/pue-rentals'),
      isAdmin ? api.get('/job-cards/') : Promise.resolve(null)
    ])

    const addDetails = (result, path, idField) => {
      if (result.status !== 'fulfilled' || !result.value?.data) return
      const data = Array.isArray(result.value.data) ? result.value.data : result.value.data.items || result.value.data.batteries || result.value.data.users || result.value.data.pue_equipment || result.value.data.rentals || result.value.data.cards || []
      for (const endpoint of getDetailEndpoints(data, path, idField)) {
        detailTasks.push(() => api.get(endpoint).catch(() => null))
      }
    }

    addDetails(batteriesRes, '/batteries', 'battery_id')
    addDetails(usersRes, '/users', 'user_id')
    addDetails(pueRes, '/pue', 'pue_id')
    addDetails(batteryRentalsRes, '/battery-rentals', 'rental_id')
    addDetails(pueRentalsRes, '/pue-rentals', 'pue_rental_id')
    if (isAdmin) {
      addDetails(jobCardsRes, '/job-cards', 'card_id')
    }
  } catch {
    // Phase 2 is best-effort
  }

  if (detailTasks.length > 0) {
    await runWithConcurrency(detailTasks, CONCURRENCY)
  }
  console.log(`[CacheWarmer] Phase 2 done: ${detailTasks.length} detail endpoints`)

  // Phase 3: Fetch sub-resources for individual items (notes, inspections, rentals, accounts)
  const SUB_RESOURCE_CAP = 20
  const subResourceTasks = []

  try {
    const addSubResources = (result, idField, subPaths) => {
      if (result.status !== 'fulfilled' || !result.value?.data) return
      const data = Array.isArray(result.value.data) ? result.value.data : result.value.data.items || []
      const items = data.slice(0, SUB_RESOURCE_CAP)
      for (const item of items) {
        const id = item[idField]
        if (!id) continue
        for (const sub of subPaths) {
          subResourceTasks.push(() => api.get(sub(id)).catch(() => null))
        }
      }
    }

    addSubResources(batteriesRes, 'battery_id', [
      (id) => `/batteries/${id}/notes`,
      (id) => `/battery-rentals?battery_id=${id}`
    ])

    addSubResources(pueRes, 'pue_id', [
      (id) => `/pue/${id}/inspections`,
      (id) => `/pue-rentals?pue_id=${id}`
    ])

    addSubResources(usersRes, 'user_id', [
      (id) => `/accounts/user/${id}`,
      (id) => `/users/${id}/subscriptions`
    ])

    addSubResources(pueRentalsRes, 'pue_rental_id', [
      (id) => `/pue-rentals/${id}/ownership-status`
    ])
  } catch {
    // Phase 3 is best-effort
  }

  if (subResourceTasks.length > 0) {
    await runWithConcurrency(subResourceTasks, CONCURRENCY)
  }
  console.log(`[CacheWarmer] Phase 3 done: ${subResourceTasks.length} sub-resource endpoints`)

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1)
  const totalEndpoints = listEndpoints.length + detailTasks.length + subResourceTasks.length
  console.log(`[CacheWarmer] Complete: ${totalEndpoints} endpoints cached in ${elapsed}s`)
}
