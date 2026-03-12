import {
  getNextTempId,
  mergeItemIntoCache,
  updateItemInCache,
  removeItemFromCache,
  getCachedResponse,
  setCachedResponse,
  invalidateCacheByPrefix
} from './offlineDb.js'

// Detect resource type from URL path and intended action
function parseResourceFromUrl (url, method) {
  const path = url.replace(/^https?:\/\/[^/]+/, '')
  const m = (method || 'post').toLowerCase()

  // --- Item-level patterns (PUT/PATCH/DELETE to resource/id) ---

  // Users: /users/{id}
  const userItemMatch = path.match(/^\/users\/([^/?]+)\/?(\?|$)/)
  if (userItemMatch && (m === 'put' || m === 'patch')) return { resource: 'user', action: 'update', id: userItemMatch[1] }
  if (userItemMatch && m === 'delete') return { resource: 'user', action: 'delete', id: userItemMatch[1] }

  // Batteries: /batteries/{id}
  const batteryItemMatch = path.match(/^\/batteries\/([^/?]+)\/?(\?|$)/)
  if (batteryItemMatch && (m === 'put' || m === 'patch')) return { resource: 'battery', action: 'update', id: batteryItemMatch[1] }
  if (batteryItemMatch && m === 'delete') return { resource: 'battery', action: 'delete', id: batteryItemMatch[1] }

  // PUE: /pue/{id} (not /pue/{id}/inspections)
  const pueItemMatch = path.match(/^\/pue\/([^/?]+)\/?(\?|$)/)
  if (pueItemMatch && (m === 'put' || m === 'patch')) return { resource: 'pue', action: 'update', id: pueItemMatch[1] }
  if (pueItemMatch && m === 'delete') return { resource: 'pue', action: 'delete', id: pueItemMatch[1] }

  // PUE inspections: POST /pue/{id}/inspections
  const pueInspectionMatch = path.match(/^\/pue\/([^/]+)\/inspections/)
  if (pueInspectionMatch && m === 'post') return { resource: 'inspection', action: 'create', parentId: pueInspectionMatch[1] }

  // Battery notes: POST /batteries/{id}/notes
  const batteryNoteMatch = path.match(/^\/batteries\/([^/]+)\/notes/)
  if (batteryNoteMatch && m === 'post') return { resource: 'battery-note', action: 'create', parentId: batteryNoteMatch[1] }

  // Job cards: /job-cards/{id}
  const jobCardItemMatch = path.match(/^\/job-cards\/([^/?]+)\/?(\?|$)/)
  if (jobCardItemMatch && (m === 'put' || m === 'patch')) return { resource: 'job-card', action: 'update', id: jobCardItemMatch[1] }
  if (jobCardItemMatch && m === 'delete') return { resource: 'job-card', action: 'delete', id: jobCardItemMatch[1] }

  // Account transactions: POST /accounts/user/{id}/transaction
  const accountTxMatch = path.match(/^\/accounts\/user\/([^/]+)\/transaction/)
  if (accountTxMatch && m === 'post') return { resource: 'account-transaction', action: 'create', userId: accountTxMatch[1] }

  // Account payments: POST /accounts/user/{id}/payment
  const accountPayMatch = path.match(/^\/accounts\/user\/([^/]+)\/payment/)
  if (accountPayMatch && m === 'post') return { resource: 'account-transaction', action: 'create', userId: accountPayMatch[1] }

  // Account manual adjustments: POST /accounts/user/{id}/manual-adjustment
  const accountAdjMatch = path.match(/^\/accounts\/user\/([^/]+)\/manual-adjustment/)
  if (accountAdjMatch && m === 'post') return { resource: 'account-transaction', action: 'create', userId: accountAdjMatch[1] }

  // Notification mark-read: PUT /notifications/{id}/read
  const notifReadMatch = path.match(/^\/notifications\/([^/]+)\/read/)
  if (notifReadMatch) return { resource: 'notification', action: 'mark-read', id: notifReadMatch[1] }

  // Notification mark-all-read: PUT /notifications/mark-all-read
  if (/^\/notifications\/mark-all-read/.test(path)) return { resource: 'notification', action: 'mark-all-read' }

  // --- Collection-level patterns (POST = create) ---

  if (/^\/users\/?(\?|$)/.test(path)) return { resource: 'user', action: 'create' }
  if (/^\/batteries\/?(\?|$)/.test(path)) return { resource: 'battery', action: 'create' }
  if (/^\/pue\/?(\?|$)/.test(path)) return { resource: 'pue', action: 'create' }
  if (/^\/battery-rentals\/?(\?|$)/.test(path)) return { resource: 'battery-rental', action: 'create' }
  if (/^\/pue-rentals\/?(\?|$)/.test(path)) return { resource: 'pue-rental', action: 'create' }
  if (/^\/job-cards\/?(\?|$)/.test(path)) return { resource: 'job-card', action: 'create' }
  if (/^\/notifications\/?(\?|$)/.test(path)) return { resource: 'notification', action: 'create' }

  // Cost structures: POST /settings/cost-structures
  if (/^\/settings\/cost-structures\/?(\?|$)/.test(path) && m === 'post') return { resource: 'cost-structure', action: 'create' }

  // Return actions
  const batteryReturnMatch = path.match(/^\/battery-rentals\/([^/]+)\/return/)
  if (batteryReturnMatch) return { resource: 'battery-rental', action: 'return', id: batteryReturnMatch[1] }

  const pueReturnMatch = path.match(/^\/pue-rentals\/([^/]+)\/return/)
  if (pueReturnMatch) return { resource: 'pue-rental', action: 'return', id: pueReturnMatch[1] }

  // Payment actions
  const batteryPaymentMatch = path.match(/^\/battery-rentals\/([^/]+)\/payment/)
  if (batteryPaymentMatch) return { resource: 'battery-rental', action: 'payment', id: batteryPaymentMatch[1] }

  const puePaymentMatch = path.match(/^\/pue-rentals\/([^/]+)\/payment/)
  if (puePaymentMatch) return { resource: 'pue-rental', action: 'payment', id: puePaymentMatch[1] }

  // Survey submission
  if (/^\/return-survey\/responses\/?(\?|$)/.test(path)) return { resource: 'survey', action: 'create' }

  return null
}

// Handle user creation: generate temp ID, build synthetic user, update caches
async function handleUserCreate (data) {
  const tempId = await getNextTempId()

  const syntheticUser = {
    ...data,
    user_id: tempId,
    username: data.username || '',
    Name: [data.first_names, data.last_name].filter(Boolean).join(' ') || data.username || '',
    first_names: data.first_names || '',
    last_name: data.last_name || '',
    mobile_number: data.mobile_number || '',
    email: data.email || '',
    hub_id: data.hub_id || null,
    user_access_level: data.user_access_level || 'customer',
    _offlineCreated: true
  }

  // Merge into all cached user lists
  await mergeItemIntoCache('GET:/users/', syntheticUser)
  await mergeItemIntoCache('GET:/users?', syntheticUser)

  // Cache detail page so navigating to the user works offline
  await setCachedResponse(`GET:/users/${tempId}`, `/users/${tempId}`, syntheticUser, 200)

  // Merge into hub-specific user list
  if (data.hub_id) {
    await mergeItemIntoCache(`GET:/hubs/${data.hub_id}/users`, syntheticUser)
  }

  return { tempId, syntheticData: syntheticUser }
}

// Handle battery creation: generate temp ID, update caches
async function handleBatteryCreate (data) {
  const tempId = await getNextTempId()

  const syntheticBattery = {
    ...data,
    battery_id: String(tempId),
    id: tempId,
    short_id: `TEMP${Math.abs(tempId)}`,
    status: 'available',
    hub_id: data.hub_id || null,
    battery_capacity_wh: data.battery_capacity_wh || null,
    model: data.model || '',
    _offlineCreated: true
  }

  await mergeItemIntoCache('GET:/batteries/', syntheticBattery)
  await mergeItemIntoCache('GET:/batteries?', syntheticBattery)
  await setCachedResponse(`GET:/batteries/${tempId}`, `/batteries/${tempId}`, syntheticBattery, 200)
  if (data.hub_id) {
    await mergeItemIntoCache(`GET:/hubs/${data.hub_id}/batteries`, syntheticBattery)
  }

  return { tempId, syntheticData: syntheticBattery }
}

// Handle PUE creation
async function handlePueCreate (data) {
  const tempId = await getNextTempId()

  const syntheticPue = {
    ...data,
    id: tempId,
    pue_id: tempId,
    status: 'available',
    hub_id: data.hub_id || null,
    _offlineCreated: true
  }

  await mergeItemIntoCache('GET:/pue/', syntheticPue)
  await mergeItemIntoCache('GET:/pue?', syntheticPue)
  await setCachedResponse(`GET:/pue/${tempId}`, `/pue/${tempId}`, syntheticPue, 200)
  if (data.hub_id) {
    await mergeItemIntoCache(`GET:/hubs/${data.hub_id}/pue`, syntheticPue)
  }

  return { tempId, syntheticData: syntheticPue }
}

// Handle battery rental creation: update battery status to rented
async function handleBatteryRentalCreate (data) {
  const tempId = await getNextTempId()

  // Mark rented batteries as unavailable in cache
  const batteryIds = data.battery_ids || []
  for (const batId of batteryIds) {
    await updateItemInCache('GET:/batteries/', 'battery_id', String(batId), { status: 'rented' })
    await updateItemInCache('GET:/batteries?', 'battery_id', String(batId), { status: 'rented' })
    // Also update hub battery lists
    await updateItemInCache('GET:/hubs/', 'battery_id', String(batId), { status: 'rented' })
  }

  const now = new Date().toISOString()
  const syntheticRental = {
    ...data,
    rental_id: tempId,
    rentral_id: tempId,
    id: tempId,
    user_id: data.user_id,
    user: { user_id: data.user_id, Name: data.user_name || `User ${data.user_id}` },
    battery_ids: data.battery_ids || [],
    battery_id: (data.battery_ids || [])[0] || null,
    hub_id: data.hub_id,
    status: 'active',
    rental_type: 'battery',
    timestamp_taken: data.rental_start_date || now,
    rental_start_date: data.rental_start_date || now,
    start_date: data.rental_start_date || now,
    due_back: data.due_date || null,
    _offlineCreated: true
  }

  await mergeItemIntoCache('GET:/battery-rentals', syntheticRental)
  await mergeItemIntoCache('GET:/rentals/', syntheticRental)
  await setCachedResponse(`GET:/battery-rentals/${tempId}`, `/battery-rentals/${tempId}`, syntheticRental, 200)

  return { tempId, syntheticData: syntheticRental }
}

// Handle PUE rental creation
async function handlePueRentalCreate (data) {
  const tempId = await getNextTempId()

  // Mark PUE as rented
  if (data.pue_id) {
    await updateItemInCache('GET:/pue/', 'pue_id', String(data.pue_id), { status: 'rented' })
    await updateItemInCache('GET:/pue?', 'pue_id', String(data.pue_id), { status: 'rented' })
    // Also update hub PUE cache entries
    await updateItemInCache('GET:/hubs/', 'pue_id', String(data.pue_id), { status: 'rented' })
  }

  const now = new Date().toISOString()
  const syntheticRental = {
    ...data,
    rental_id: tempId,
    pue_rental_id: tempId,
    id: tempId,
    user_id: data.user_id,
    user: { user_id: data.user_id, Name: data.user_name || `User ${data.user_id}` },
    pue_id: data.pue_id,
    pue_name: data.pue_name || `PUE ${data.pue_id}`,
    hub_id: data.hub_id,
    status: 'active',
    rental_type: 'pue',
    timestamp_taken: data.rental_start_date || now,
    rental_start_date: data.rental_start_date || now,
    due_back: data.due_date || null,
    _offlineCreated: true
  }

  await mergeItemIntoCache('GET:/pue-rentals', syntheticRental)
  await mergeItemIntoCache('GET:/rentals/', syntheticRental)
  await setCachedResponse(`GET:/pue-rentals/${tempId}`, `/pue-rentals/${tempId}`, syntheticRental, 200)

  return { tempId, syntheticData: syntheticRental }
}

// Handle battery rental return: update battery status back to available
async function handleBatteryReturn (rentalId) {
  // Find the rental in cache to get battery IDs
  const rentalCache = await getCachedResponse(`GET:/battery-rentals/${rentalId}`)
  let batteryIds = []

  if (rentalCache && rentalCache.data) {
    batteryIds = rentalCache.data.battery_ids || rentalCache.data.batteries?.map(b => b.battery_id) || []
  }

  // Also scan the rental list cache
  if (batteryIds.length === 0) {
    const listCache = await getCachedResponse('GET:/battery-rentals')
    if (listCache && Array.isArray(listCache.data)) {
      const rental = listCache.data.find(r =>
        String(r.rental_id) === String(rentalId) || String(r.id) === String(rentalId)
      )
      if (rental) {
        batteryIds = rental.battery_ids || []
      }
    }
  }

  // Mark batteries as available again
  for (const batId of batteryIds) {
    await updateItemInCache('GET:/batteries/', 'battery_id', String(batId), { status: 'available' })
    await updateItemInCache('GET:/batteries?', 'battery_id', String(batId), { status: 'available' })
  }

  // Update rental status in cache (include date_returned so status filters work)
  const returnUpdates = { status: 'returned', actual_return_date: new Date().toISOString() }
  await updateItemInCache('GET:/battery-rentals', 'rental_id', Number(rentalId), returnUpdates)
  await updateItemInCache('GET:/rentals/', 'rental_id', Number(rentalId), returnUpdates)

  return { tempId: null, syntheticData: { rental_id: Number(rentalId), status: 'returned', _offlineQueued: true } }
}

// Handle PUE rental return
async function handlePueReturn (rentalId) {
  // Find rental to get PUE ID
  const rentalCache = await getCachedResponse(`GET:/pue-rentals/${rentalId}`)
  let pueId = null

  if (rentalCache && rentalCache.data) {
    pueId = rentalCache.data.pue_id
  }

  if (!pueId) {
    const listCache = await getCachedResponse('GET:/pue-rentals')
    if (listCache && Array.isArray(listCache.data)) {
      const rental = listCache.data.find(r =>
        String(r.pue_rental_id) === String(rentalId) || String(r.rental_id) === String(rentalId)
      )
      if (rental) pueId = rental.pue_id
    }
  }

  // Mark PUE as available
  if (pueId) {
    await updateItemInCache('GET:/pue/', 'pue_id', String(pueId), { status: 'available' })
    await updateItemInCache('GET:/pue?', 'pue_id', String(pueId), { status: 'available' })
    // Also update the /hubs/ PUE cache entries
    await updateItemInCache('GET:/hubs/', 'pue_id', String(pueId), { status: 'available' })
  }

  // Update by pue_rental_id (PUE rentals use this field, not rental_id)
  const rentalIdNum = Number(rentalId)
  await updateItemInCache('GET:/pue-rentals', 'pue_rental_id', rentalIdNum, { status: 'returned', date_returned: new Date().toISOString(), is_active: false })

  return { tempId: null, syntheticData: { pue_rental_id: rentalIdNum, status: 'returned', _offlineQueued: true } }
}

// Handle job card creation
async function handleJobCardCreate (data) {
  const tempId = await getNextTempId()

  const syntheticJobCard = {
    ...data,
    id: tempId,
    card_id: tempId,
    status: data.status || 'todo',
    created_at: new Date().toISOString(),
    _offlineCreated: true
  }

  await mergeItemIntoCache('GET:/job-cards/', syntheticJobCard)
  await setCachedResponse(`GET:/job-cards/${tempId}`, `/job-cards/${tempId}`, syntheticJobCard, 200)

  return { tempId, syntheticData: syntheticJobCard }
}

// --- Generic update/delete handlers ---

// Handle user update: merge updated fields into cached lists and detail
async function handleUserUpdate (id, data) {
  await updateItemInCache('GET:/users/', 'user_id', Number(id), data)
  await updateItemInCache('GET:/users?', 'user_id', Number(id), data)

  // Update detail cache
  const detail = await getCachedResponse(`GET:/users/${id}`)
  if (detail) {
    await setCachedResponse(`GET:/users/${id}`, `/users/${id}`, { ...detail.data, ...data }, 200)
  }

  // Update hub-specific lists
  const hubId = data.hub_id || detail?.data?.hub_id
  if (hubId) {
    await updateItemInCache(`GET:/hubs/${hubId}/users`, 'user_id', Number(id), data)
  }

  return { tempId: null, syntheticData: { user_id: Number(id), ...data, _offlineQueued: true } }
}

// Handle user delete: remove from cached lists and detail
async function handleUserDelete (id) {
  await removeItemFromCache('GET:/users/', 'user_id', Number(id))
  await removeItemFromCache('GET:/users?', 'user_id', Number(id))
  await invalidateCacheByPrefix(`GET:/users/${id}`)
  return { tempId: null, syntheticData: { _offlineQueued: true } }
}

// Handle battery update
async function handleBatteryUpdate (id, data) {
  await updateItemInCache('GET:/batteries/', 'battery_id', String(id), data)
  await updateItemInCache('GET:/batteries?', 'battery_id', String(id), data)

  const detail = await getCachedResponse(`GET:/batteries/${id}`)
  if (detail) {
    await setCachedResponse(`GET:/batteries/${id}`, `/batteries/${id}`, { ...detail.data, ...data }, 200)
  }

  const hubId = data.hub_id || detail?.data?.hub_id
  if (hubId) {
    await updateItemInCache(`GET:/hubs/${hubId}/batteries`, 'battery_id', String(id), data)
  }

  return { tempId: null, syntheticData: { battery_id: String(id), ...data, _offlineQueued: true } }
}

// Handle battery delete
async function handleBatteryDelete (id) {
  await removeItemFromCache('GET:/batteries/', 'battery_id', String(id))
  await removeItemFromCache('GET:/batteries?', 'battery_id', String(id))
  await invalidateCacheByPrefix(`GET:/batteries/${id}`)
  return { tempId: null, syntheticData: { _offlineQueued: true } }
}

// Handle PUE update
async function handlePueUpdate (id, data) {
  await updateItemInCache('GET:/pue/', 'id', Number(id), data)
  await updateItemInCache('GET:/pue?', 'id', Number(id), data)

  const detail = await getCachedResponse(`GET:/pue/${id}`)
  if (detail) {
    await setCachedResponse(`GET:/pue/${id}`, `/pue/${id}`, { ...detail.data, ...data }, 200)
  }

  const hubId = data.hub_id || detail?.data?.hub_id
  if (hubId) {
    await updateItemInCache(`GET:/hubs/${hubId}/pue`, 'id', Number(id), data)
  }

  return { tempId: null, syntheticData: { id: Number(id), ...data, _offlineQueued: true } }
}

// Handle PUE delete
async function handlePueDelete (id) {
  await removeItemFromCache('GET:/pue/', 'id', Number(id))
  await removeItemFromCache('GET:/pue?', 'id', Number(id))
  await invalidateCacheByPrefix(`GET:/pue/${id}`)
  return { tempId: null, syntheticData: { _offlineQueued: true } }
}

// Handle job card update
async function handleJobCardUpdate (id, data) {
  await updateItemInCache('GET:/job-cards/', 'id', Number(id), data)

  const detail = await getCachedResponse(`GET:/job-cards/${id}`)
  if (detail) {
    await setCachedResponse(`GET:/job-cards/${id}`, `/job-cards/${id}`, { ...detail.data, ...data }, 200)
  }

  return { tempId: null, syntheticData: { id: Number(id), ...data, _offlineQueued: true } }
}

// Handle job card delete
async function handleJobCardDelete (id) {
  await removeItemFromCache('GET:/job-cards/', 'id', Number(id))
  await invalidateCacheByPrefix(`GET:/job-cards/${id}`)
  return { tempId: null, syntheticData: { _offlineQueued: true } }
}

// Handle PUE inspection creation
async function handleInspectionCreate (pueId, data) {
  const tempId = await getNextTempId()

  const syntheticInspection = {
    ...data,
    id: tempId,
    pue_id: Number(pueId),
    inspection_date: data.inspection_date || new Date().toISOString(),
    status: data.status || 'completed',
    _offlineCreated: true
  }

  // Update PUE's last_inspection_date in cache
  await updateItemInCache('GET:/pue/', 'id', Number(pueId), {
    last_inspection_date: syntheticInspection.inspection_date
  })
  await updateItemInCache('GET:/pue?', 'id', Number(pueId), {
    last_inspection_date: syntheticInspection.inspection_date
  })

  return { tempId, syntheticData: syntheticInspection }
}

// Handle notification mark as read
async function handleNotificationMarkRead (id) {
  await updateItemInCache('GET:/notifications', 'id', Number(id), { read: true, read_at: new Date().toISOString() })
  return { tempId: null, syntheticData: { id: Number(id), read: true, _offlineQueued: true } }
}

// Handle mark all notifications as read
async function handleNotificationMarkAllRead () {
  // Invalidate all notification caches so they re-fetch on next online
  await invalidateCacheByPrefix('GET:/notifications')
  return { tempId: null, syntheticData: { _offlineQueued: true } }
}

// Handle notification creation
async function handleNotificationCreate (data) {
  const tempId = await getNextTempId()
  const syntheticNotification = {
    ...data,
    id: tempId,
    read: false,
    created_at: new Date().toISOString(),
    _offlineCreated: true
  }
  await mergeItemIntoCache('GET:/notifications', syntheticNotification)
  return { tempId, syntheticData: syntheticNotification }
}

// Handle cost structure creation: make it available for rental forms offline
async function handleCostStructureCreate (data) {
  const tempId = await getNextTempId()

  const syntheticStructure = {
    ...data,
    structure_id: tempId,
    id: tempId,
    is_active: true,
    components: data.components ? (typeof data.components === 'string' ? JSON.parse(data.components) : data.components) : [],
    duration_options: data.duration_options ? (typeof data.duration_options === 'string' ? JSON.parse(data.duration_options) : data.duration_options) : [],
    _offlineCreated: true
  }

  await mergeItemIntoCache('GET:/settings/cost-structures', syntheticStructure)

  return { tempId, syntheticData: syntheticStructure }
}

// Handle account transaction creation
async function handleAccountTransaction (userId, data) {
  // Invalidate the account summary cache so it re-fetches on sync
  await invalidateCacheByPrefix(`GET:/accounts/hub/`)
  await invalidateCacheByPrefix(`GET:/accounts/users/in-debt`)

  return { tempId: null, syntheticData: { user_id: Number(userId), ...data, _offlineQueued: true } }
}

/**
 * Process an offline mutation optimistically.
 * Returns { tempId, syntheticData } for the interceptor to use.
 * Returns null if no special handling is needed.
 */
export async function processOptimisticMutation (method, url, data) {
  const parsed = parseResourceFromUrl(url, method)
  if (!parsed) return null

  const m = method.toLowerCase()

  try {
    // Creates (POST to collection)
    if (m === 'post' && parsed.action === 'create') {
      switch (parsed.resource) {
        case 'user': return await handleUserCreate(data || {})
        case 'battery': return await handleBatteryCreate(data || {})
        case 'pue': return await handlePueCreate(data || {})
        case 'battery-rental': return await handleBatteryRentalCreate(data || {})
        case 'pue-rental': return await handlePueRentalCreate(data || {})
        case 'job-card': return await handleJobCardCreate(data || {})
        case 'notification': return await handleNotificationCreate(data || {})
        case 'inspection': return await handleInspectionCreate(parsed.parentId, data || {})
        case 'account-transaction': return await handleAccountTransaction(parsed.userId, data || {})
        case 'cost-structure': return await handleCostStructureCreate(data || {})
        case 'survey': return { tempId: null, syntheticData: { _offlineQueued: true } }
      }
    }

    // Updates (PUT/PATCH to item)
    if ((m === 'put' || m === 'patch') && parsed.action === 'update') {
      switch (parsed.resource) {
        case 'user': return await handleUserUpdate(parsed.id, data || {})
        case 'battery': return await handleBatteryUpdate(parsed.id, data || {})
        case 'pue': return await handlePueUpdate(parsed.id, data || {})
        case 'job-card': return await handleJobCardUpdate(parsed.id, data || {})
      }
    }

    // Deletes (DELETE to item)
    if (m === 'delete' && parsed.action === 'delete') {
      switch (parsed.resource) {
        case 'user': return await handleUserDelete(parsed.id)
        case 'battery': return await handleBatteryDelete(parsed.id)
        case 'pue': return await handlePueDelete(parsed.id)
        case 'job-card': return await handleJobCardDelete(parsed.id)
      }
    }

    // Returns (POST to item/return)
    if (m === 'post' && parsed.action === 'return') {
      if (parsed.resource === 'battery-rental') return await handleBatteryReturn(parsed.id)
      if (parsed.resource === 'pue-rental') return await handlePueReturn(parsed.id)
    }

    // Payments and other actions
    if (m === 'post' && parsed.action === 'payment') {
      return { tempId: null, syntheticData: { _offlineQueued: true } }
    }

    // Notification mark-read
    if (parsed.action === 'mark-read') {
      return await handleNotificationMarkRead(parsed.id)
    }
    if (parsed.action === 'mark-all-read') {
      return await handleNotificationMarkAllRead()
    }
  } catch (e) {
    // Optimistic updates are best-effort; don't block queuing
    console.warn('Optimistic update failed:', e)
  }

  return null
}
