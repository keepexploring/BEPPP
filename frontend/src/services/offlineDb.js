import { openDB } from 'idb'

const DB_NAME = 'beppp-offline'
const DB_VERSION = 1

// TTL strategy by URL pattern (in milliseconds)
const TTL_RULES = [
  { pattern: /\/settings\//, ttl: 60 * 60 * 1000 },       // 60min
  { pattern: /\/hubs\//, ttl: 30 * 60 * 1000 },            // 30min
  { pattern: /\/users\//, ttl: 15 * 60 * 1000 },           // 15min
  { pattern: /\/batteries\//, ttl: 5 * 60 * 1000 },        // 5min
  { pattern: /\/pue\//, ttl: 5 * 60 * 1000 },              // 5min
  { pattern: /\/rentals\//, ttl: 2 * 60 * 1000 },          // 2min
  { pattern: /\/battery-rentals/, ttl: 2 * 60 * 1000 },    // 2min
  { pattern: /\/pue-rentals/, ttl: 2 * 60 * 1000 },        // 2min
  { pattern: /\/data\//, ttl: 60 * 1000 },                 // 1min (telemetry)
  { pattern: /\/analytics\//, ttl: 5 * 60 * 1000 },        // 5min
  { pattern: /\/notifications/, ttl: 2 * 60 * 1000 },      // 2min
  { pattern: /\/job-cards\//, ttl: 5 * 60 * 1000 },        // 5min
  { pattern: /\/accounts\//, ttl: 5 * 60 * 1000 },         // 5min
  { pattern: /\/inspections\//, ttl: 5 * 60 * 1000 },      // 5min
  { pattern: /\/return-survey\//, ttl: 5 * 60 * 1000 },    // 5min
  { pattern: /\/subscriptions/, ttl: 5 * 60 * 1000 },      // 5min
]

const DEFAULT_TTL = 5 * 60 * 1000 // 5min default

let dbPromise = null

export function openDb () {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade (db) {
        // API response cache
        if (!db.objectStoreNames.contains('apiCache')) {
          db.createObjectStore('apiCache', { keyPath: 'cacheKey' })
        }
        // Offline mutation queue
        if (!db.objectStoreNames.contains('mutationQueue')) {
          const store = db.createObjectStore('mutationQueue', {
            keyPath: 'id',
            autoIncrement: true
          })
          store.createIndex('status', 'status')
        }
        // Sync metadata (key-value)
        if (!db.objectStoreNames.contains('syncMeta')) {
          db.createObjectStore('syncMeta', { keyPath: 'key' })
        }
      }
    })
  }
  return dbPromise
}

/**
 * Build a cache key from method + URL path (strips query params for cleaner matching)
 */
export function buildCacheKey (method, url) {
  // Remove base URL if present, keep only path + query
  let path = url
  try {
    const parsed = new URL(url)
    path = parsed.pathname + parsed.search
  } catch {
    // url is already a relative path
  }
  return `${method.toUpperCase()}:${path}`
}

/**
 * Determine TTL for a URL based on pattern matching
 */
export function getTtlForUrl (url) {
  for (const rule of TTL_RULES) {
    if (rule.pattern.test(url)) {
      return rule.ttl
    }
  }
  return DEFAULT_TTL
}

/**
 * Get a cached API response by cache key.
 * When ignoreExpiry is true, returns stale data rather than nothing (used when offline).
 */
export async function getCachedResponse (cacheKey, { ignoreExpiry = false } = {}) {
  const db = await openDb()
  const entry = await db.get('apiCache', cacheKey)
  if (!entry) return null

  // Check TTL expiry (skip when offline — stale data beats no data)
  if (!ignoreExpiry) {
    const age = Date.now() - entry.cachedAt
    if (age > entry.ttl) {
      return null // Expired, but don't delete yet (cleanup handles that)
    }
  }

  return entry
}

/**
 * Store an API response in the cache
 */
export async function setCachedResponse (cacheKey, url, data, status) {
  const db = await openDb()
  await db.put('apiCache', {
    cacheKey,
    url,
    data,
    status,
    cachedAt: Date.now(),
    ttl: getTtlForUrl(url)
  })
}

/**
 * Delete specific cache entries by key prefix (e.g. "GET:/batteries")
 */
export async function invalidateCacheByPrefix (prefix) {
  const db = await openDb()
  const tx = db.transaction('apiCache', 'readwrite')
  const store = tx.objectStore('apiCache')
  let cursor = await store.openCursor()
  while (cursor) {
    if (cursor.key.startsWith(prefix)) {
      await cursor.delete()
    }
    cursor = await cursor.continue()
  }
  await tx.done
}

/**
 * Delete cache entries matching a regex pattern
 */
export async function invalidateCacheByPattern (pattern) {
  const db = await openDb()
  const tx = db.transaction('apiCache', 'readwrite')
  const store = tx.objectStore('apiCache')
  let cursor = await store.openCursor()
  while (cursor) {
    if (pattern.test(cursor.key)) {
      await cursor.delete()
    }
    cursor = await cursor.continue()
  }
  await tx.done
}

/**
 * Remove all expired cache entries
 */
export async function clearExpiredCache () {
  const db = await openDb()
  const tx = db.transaction('apiCache', 'readwrite')
  const store = tx.objectStore('apiCache')
  let cursor = await store.openCursor()
  const now = Date.now()
  while (cursor) {
    const entry = cursor.value
    if (now - entry.cachedAt > entry.ttl) {
      await cursor.delete()
    }
    cursor = await cursor.continue()
  }
  await tx.done
}

/**
 * Add a mutation to the offline queue.
 * Optionally includes a tempId for create operations.
 */
export async function addToMutationQueue (mutation) {
  const db = await openDb()
  return db.add('mutationQueue', {
    method: mutation.method,
    url: mutation.url,
    data: mutation.data || null,
    headers: mutation.headers || {},
    createdAt: Date.now(),
    retryCount: 0,
    status: 'pending',
    tempId: mutation.tempId || null
  })
}

/**
 * Get all pending mutations from the queue (FIFO order)
 */
export async function getMutationQueue () {
  const db = await openDb()
  const all = await db.getAll('mutationQueue')
  return all
    .filter(m => m.status === 'pending')
    .sort((a, b) => a.id - b.id)
}

/**
 * Get count of all pending mutations
 */
export async function getPendingMutationCount () {
  const db = await openDb()
  const all = await db.getAll('mutationQueue')
  return all.filter(m => m.status === 'pending').length
}

/**
 * Get all failed mutations from the queue
 */
export async function getFailedMutations () {
  const db = await openDb()
  const all = await db.getAll('mutationQueue')
  return all.filter(m => m.status === 'failed')
}

/**
 * Get count of failed mutations
 */
export async function getFailedMutationCount () {
  const db = await openDb()
  const all = await db.getAll('mutationQueue')
  return all.filter(m => m.status === 'failed').length
}

/**
 * Update a mutation in the queue
 */
export async function updateMutation (id, updates) {
  const db = await openDb()
  const mutation = await db.get('mutationQueue', id)
  if (!mutation) return
  Object.assign(mutation, updates)
  await db.put('mutationQueue', mutation)
}

/**
 * Remove a mutation from the queue
 */
export async function removeMutation (id) {
  const db = await openDb()
  await db.delete('mutationQueue', id)
}

/**
 * Get/set sync metadata
 */
export async function getSyncMeta (key) {
  const db = await openDb()
  const entry = await db.get('syncMeta', key)
  return entry ? entry.value : null
}

export async function setSyncMeta (key, value) {
  const db = await openDb()
  await db.put('syncMeta', { key, value })
}

// ── Temp ID system for offline entity chaining ──

/**
 * Get the next temporary ID (negative integers: -1, -2, -3, ...)
 */
export async function getNextTempId () {
  const current = (await getSyncMeta('nextTempId')) || 0
  const next = current - 1
  await setSyncMeta('nextTempId', next)
  return next
}

/**
 * Record a mapping from temp ID to real server ID after sync.
 */
export async function addTempIdMapping (tempId, realId) {
  const mappings = (await getSyncMeta('tempIdMappings')) || {}
  mappings[String(tempId)] = realId
  await setSyncMeta('tempIdMappings', mappings)
}

/**
 * Get all temp-to-real ID mappings.
 */
export async function getTempIdMappings () {
  return (await getSyncMeta('tempIdMappings')) || {}
}

/**
 * Clear all temp ID mappings (after full sync).
 */
export async function clearTempIdMappings () {
  await setSyncMeta('tempIdMappings', {})
}

// ── Optimistic cache mutations ──

/**
 * Append an item to all cached arrays whose key matches the prefix.
 * All list endpoints return plain arrays, so we push directly.
 */
export async function mergeItemIntoCache (cacheKeyPrefix, newItem) {
  const db = await openDb()
  const tx = db.transaction('apiCache', 'readwrite')
  const store = tx.objectStore('apiCache')
  let cursor = await store.openCursor()
  while (cursor) {
    if (cursor.key.startsWith(cacheKeyPrefix)) {
      const entry = { ...cursor.value }
      let merged = false
      if (Array.isArray(entry.data)) {
        entry.data = [...entry.data, newItem]
        merged = true
      } else if (entry.data && typeof entry.data === 'object') {
        // Handle wrapped responses like { cards: [...], total: N }
        for (const key of Object.keys(entry.data)) {
          if (Array.isArray(entry.data[key])) {
            entry.data = { ...entry.data, [key]: [...entry.data[key], newItem] }
            merged = true
            break
          }
        }
      }
      if (merged) {
        entry.cachedAt = Date.now()
        await cursor.update(entry)
      }
    }
    cursor = await cursor.continue()
  }
  await tx.done
}

/**
 * Update items in cached arrays matching the given criteria.
 * Finds items where item[idField] === idValue and applies updates.
 */
export async function updateItemInCache (cacheKeyPrefix, idField, idValue, updates) {
  const db = await openDb()
  const tx = db.transaction('apiCache', 'readwrite')
  const store = tx.objectStore('apiCache')
  let cursor = await store.openCursor()
  while (cursor) {
    if (cursor.key.startsWith(cacheKeyPrefix)) {
      const entry = { ...cursor.value }
      if (Array.isArray(entry.data)) {
        let changed = false
        entry.data = entry.data.map(item => {
          if (item[idField] === idValue) {
            changed = true
            return { ...item, ...updates }
          }
          return item
        })
        if (changed) {
          entry.cachedAt = Date.now()
          await cursor.update(entry)
        }
      }
    }
    cursor = await cursor.continue()
  }
  await tx.done
}

/**
 * Remove an item from cached arrays matching the given criteria.
 * Finds items where item[idField] === idValue and removes them.
 */
export async function removeItemFromCache (cacheKeyPrefix, idField, idValue) {
  const db = await openDb()
  const tx = db.transaction('apiCache', 'readwrite')
  const store = tx.objectStore('apiCache')
  let cursor = await store.openCursor()
  while (cursor) {
    if (cursor.key.startsWith(cacheKeyPrefix)) {
      const entry = { ...cursor.value }
      if (Array.isArray(entry.data)) {
        const filtered = entry.data.filter(item => item[idField] !== idValue)
        if (filtered.length !== entry.data.length) {
          entry.data = filtered
          entry.cachedAt = Date.now()
          await cursor.update(entry)
        }
      }
    }
    cursor = await cursor.continue()
  }
  await tx.done
}
