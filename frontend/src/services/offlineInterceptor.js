import {
  buildCacheKey,
  getCachedResponse,
  setCachedResponse,
  addToMutationQueue,
  getDeltaSyncConfig,
  getLastSyncTime,
  setLastSyncTime,
  mergeDeltaIntoCache,
  isConnectionFast,
  shouldForceFullRefresh,
  getLastFullRefreshTime,
  setLastFullRefreshTime
} from './offlineDb.js'
import { processOptimisticMutation } from './offlineOptimistic.js'

// Endpoints that should never be cached or queued offline
const EXCLUDED_PATTERNS = [
  /\/auth\/token/,
  /\/auth\/battery-/,
  /\/health/,
  /\/analytics\/export\//,
  /\/return-survey\/responses\/export/
]

function isExcluded (url) {
  return EXCLUDED_PATTERNS.some(p => p.test(url))
}

function isOnline () {
  return navigator.onLine
}

function isGetRequest (config) {
  return (config.method || 'get').toLowerCase() === 'get'
}

function isMutationRequest (config) {
  const method = (config.method || 'get').toLowerCase()
  return ['post', 'put', 'patch', 'delete'].includes(method)
}

function isFileUpload (config) {
  return config.data instanceof FormData
}

function isNetworkError (error) {
  return (
    !error.response &&
    (error.code === 'ERR_NETWORK' ||
     error.code === 'ERR_INTERNET_DISCONNECTED' ||
     error.code === 'ECONNABORTED' ||
     error.message === 'Network Error' ||
     error.message?.includes('timeout') ||
     error.message?.includes('ERR_INTERNET_DISCONNECTED') ||
     error.message?.includes('ERR_NAME_NOT_RESOLVED'))
  )
}

function getFullUrl (config) {
  if (config.url?.startsWith('http')) {
    return config.url
  }
  const base = (config.baseURL || '').replace(/\/$/, '')
  const path = config.url || ''
  let fullUrl = base + (path.startsWith('/') ? path : '/' + path)

  if (config.params && Object.keys(config.params).length > 0) {
    const search = new URLSearchParams()
    for (const [key, val] of Object.entries(config.params)) {
      if (val !== undefined && val !== null) {
        search.append(key, String(val))
      }
    }
    const qs = search.toString()
    if (qs) {
      fullUrl += (fullUrl.includes('?') ? '&' : '?') + qs
    }
  }
  return fullUrl
}

function syntheticResponse (data, status, config) {
  return {
    data,
    status,
    statusText: status === 202 ? 'Accepted (Offline)' : 'OK (Cached)',
    headers: {},
    config,
    _offlineResponse: true
  }
}

/**
 * Queue a mutation with optimistic updates.
 * Returns the synthetic data for the response.
 */
async function queueMutationOptimistically (method, fullUrl, requestData) {
  // Run optimistic updates (generate temp ID, update caches)
  const optimistic = await processOptimisticMutation(method, fullUrl, requestData)

  const tempId = optimistic?.tempId || null
  const syntheticData = optimistic?.syntheticData || { _offlineQueued: true }

  // Queue the mutation (include tempId if generated)
  await addToMutationQueue({
    method,
    url: fullUrl,
    data: requestData,
    headers: {},
    tempId
  })

  return { ...syntheticData, _offlineQueued: true }
}

/**
 * Install offline interceptors on the given axios instance.
 */
export function installOfflineInterceptors (axiosInstance) {
  // ── Request interceptor ──
  axiosInstance.interceptors.request.use(
    async (config) => {
      if (config._bypassOffline) return config

      const fullUrl = getFullUrl(config)
      if (isExcluded(fullUrl)) return config
      if (config.responseType === 'blob') return config

      const cacheKey = buildCacheKey(config.method || 'get', fullUrl)
      config._offlineMeta = { cacheKey, fullUrl }

      if (!isOnline()) {
        // Offline + GET: serve from cache (ignore TTL — stale data beats no data)
        if (isGetRequest(config)) {
          const cached = await getCachedResponse(cacheKey, { ignoreExpiry: true })
          if (cached) {
            return Promise.reject({
              __offlineCached: true,
              cachedData: cached.data,
              cachedStatus: cached.status,
              config
            })
          }
          return config
        }

        // Offline + file upload: reject
        if (isFileUpload(config)) {
          return Promise.reject({
            __offlineUploadBlocked: true,
            config,
            message: 'File uploads require an internet connection.'
          })
        }

        // Offline + mutation: queue with optimistic updates
        if (isMutationRequest(config)) {
          const syntheticData = await queueMutationOptimistically(
            config.method,
            fullUrl,
            config.data
          )

          return Promise.reject({
            __offlineQueued: true,
            __syntheticData: syntheticData,
            config
          })
        }
      }

      // Online + GET: stale-while-revalidate — serve cache immediately, revalidate in background
      if (isOnline() && isGetRequest(config)) {
        const cached = await getCachedResponse(cacheKey, { ignoreExpiry: true })
        // Don't serve an empty array as stale data when online — it may be a corrupted entry.
        // Fall through to a full network request so the cache can self-heal.
        const cachedIsEmptyList = Array.isArray(cached?.data) && cached.data.length === 0
        if (cached && !cachedIsEmptyList) {
          // Check if this endpoint supports delta sync
          const deltaConfig = getDeltaSyncConfig(fullUrl)
          // Strip _offlineMeta: the response interceptor uses it to write to cache, but
          // for background requests the .then() handler owns cache writes — if we left
          // it in, a delta response of [] would overwrite the full cache before merge.
          const bgConfig = { ...config, _bypassOffline: true }
          delete bgConfig._offlineMeta

          if (deltaConfig) {
            // Delta-eligible endpoint: decide delta vs full refresh
            const lastSync = await getLastSyncTime(cacheKey)
            const lastFullRefresh = await getLastFullRefreshTime(cacheKey)
            const doFullRefresh = !lastSync || (isConnectionFast() && shouldForceFullRefresh(lastFullRefresh))

            if (!doFullRefresh && lastSync) {
              // Delta fetch: add modified_after param
              bgConfig.params = { ...(bgConfig.params || {}), modified_after: lastSync }
              bgConfig._deltaSync = deltaConfig
            }
          }

          // Fire background revalidation (delta or full)
          axiosInstance(bgConfig)
            .then(async (freshResponse) => {
              if (freshResponse.status >= 200 && freshResponse.status < 300) {
                // Extract server date for clock-aligned sync timestamps
                const serverDate = freshResponse.headers?.date
                  ? new Date(freshResponse.headers.date).toISOString()
                  : new Date().toISOString()

                if (bgConfig._deltaSync) {
                  // Delta response: merge into existing cache
                  const { idField, dataPath } = bgConfig._deltaSync
                  const deltaItems = dataPath ? (freshResponse.data?.[dataPath] || []) : freshResponse.data
                  const mergedData = await mergeDeltaIntoCache(cacheKey, Array.isArray(deltaItems) ? deltaItems : [], idField, dataPath)
                  if (mergedData !== null) {
                    window.dispatchEvent(new CustomEvent('cache-updated', { detail: { url: fullUrl, data: mergedData } }))
                  }
                } else {
                  // Full fetch: replace cache entirely
                  await setCachedResponse(cacheKey, fullUrl, freshResponse.data, freshResponse.status)
                  if (deltaConfig) {
                    await setLastFullRefreshTime(cacheKey)
                  }
                  window.dispatchEvent(new CustomEvent('cache-updated', { detail: { url: fullUrl, data: freshResponse.data } }))
                }

                // Update sync time for delta-eligible endpoints
                if (deltaConfig) {
                  await setLastSyncTime(cacheKey, serverDate)
                }
              }
            })
            .catch(() => {}) // Silently ignore background fetch failures

          // Return stale cache immediately
          return Promise.reject({
            __offlineCached: true,
            cachedData: cached.data,
            cachedStatus: cached.status,
            config
          })
        }
      }

      return config
    },
    (error) => Promise.reject(error)
  )

  // ── Response interceptor (success path) ──
  axiosInstance.interceptors.response.use(
    (response) => {
      const meta = response.config?._offlineMeta
      if (meta && isGetRequest(response.config) && response.status >= 200 && response.status < 300) {
        setCachedResponse(meta.cacheKey, meta.fullUrl, response.data, response.status)
          .catch(() => {})
        // Seed sync timestamp for delta-eligible endpoints on foreground GETs
        const deltaConfig = getDeltaSyncConfig(meta.fullUrl)
        if (deltaConfig) {
          const serverDate = response.headers?.date
            ? new Date(response.headers.date).toISOString()
            : new Date().toISOString()
          setLastSyncTime(meta.cacheKey, serverDate).catch(() => {})
          setLastFullRefreshTime(meta.cacheKey).catch(() => {})
        }
      }
      return response
    },

    // ── Response interceptor (error path) ──
    async (error) => {
      if (error.__offlineCached) {
        return syntheticResponse(
          error.cachedData,
          error.cachedStatus || 200,
          error.config
        )
      }

      if (error.__offlineQueued) {
        // Notify UI that a mutation was queued
        window.dispatchEvent(new CustomEvent('offline-mutation-queued'))
        // Return the optimistic synthetic data (includes temp IDs for chaining)
        return syntheticResponse(
          error.__syntheticData || { _offlineQueued: true },
          202,
          error.config
        )
      }

      if (error.__offlineUploadBlocked) {
        return Promise.reject(error)
      }

      // Network errors while "online" (flaky connection)
      if (isNetworkError(error) && error.config) {
        const config = error.config
        const fullUrl = config._offlineMeta?.fullUrl || getFullUrl(config)
        const cacheKey = config._offlineMeta?.cacheKey || buildCacheKey(config.method || 'get', fullUrl)

        if (isExcluded(fullUrl) || config.responseType === 'blob' || config._bypassOffline) {
          return Promise.reject(error)
        }

        // GET: try cache fallback (ignore TTL — network is down)
        if (isGetRequest(config)) {
          const cached = await getCachedResponse(cacheKey, { ignoreExpiry: true })
          if (cached) {
            return syntheticResponse(cached.data, cached.status || 200, config)
          }
        }

        // Mutation: queue with optimistic updates
        if (isMutationRequest(config) && !isFileUpload(config)) {
          const syntheticData = await queueMutationOptimistically(
            config.method,
            fullUrl,
            config.data
          )
          window.dispatchEvent(new CustomEvent('offline-mutation-queued'))
          return syntheticResponse(syntheticData, 202, config)
        }
      }

      return Promise.reject(error)
    }
  )
}
