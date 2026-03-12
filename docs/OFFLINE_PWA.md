# Offline-First PWA

The Battery Hub Manager is built as a Progressive Web App (PWA) with offline-first capabilities. Field operators often work in areas with unreliable or no internet connectivity. The app caches all previously-downloaded data locally and queues any changes made while offline, syncing automatically when connectivity returns.

## Important Limitations

Before relying on offline mode, understand these constraints:

- **Login requires network**: You must be online to log in. The app only works offline after a successful login session. If your JWT token expires while offline, you'll need to reconnect to re-authenticate.

- **Last-write-wins conflict resolution**: There is no CRDT or merge logic. If two devices edit the same record while both are offline, whichever device syncs last will overwrite the other's changes. Coordinate with team members to avoid editing the same records simultaneously when offline.

- **Temporary IDs for offline-created resources**: When you create a user, battery, or rental offline, the app assigns a temporary negative ID (e.g. -1, -2). These temp IDs allow chaining operations (e.g. register user then rent a battery to them) but detail pages may not load until sync completes and real server IDs replace the temps.

- **File uploads require network**: Photo uploads (e.g. user ID photos via `uploadIdPhoto`) cannot be queued offline because `FormData` payloads are not serializable. The app will show an error if you attempt a file upload while offline.

- **Queued mutations are not editable**: Once a change is queued for sync, it cannot be modified or cancelled from the UI. It will be sent as-is when connectivity returns.

- **Failed mutations are visible and actionable**: If a queued mutation fails with a server error (5xx) after 5 retry attempts, or with a client error (4xx) on the first attempt, it is marked as failed. A red chip in the toolbar shows the count; clicking it opens a dialog where you can Retry or Discard each failed mutation.

- **Cache has TTL limits**: Cached data expires based on data type (e.g. settings: 60min, batteries: 5min, telemetry: 1min). Stale data may be shown if you've been offline longer than the TTL. Expired cache entries are cleaned up periodically.

- **Analytics exports and survey exports require network**: Blob/file downloads (CSV exports etc.) are excluded from offline caching entirely.

## Architecture

All 150+ API calls across the app flow through a single axios instance (`frontend/src/services/api.js`). The offline system intercepts at this single point using axios interceptors, making the entire app work offline transparently with zero changes to any page or component.

### Data Flow

```
Page calls someAPI.method()
  -> Offline request interceptor: tag, check connectivity, cache/queue if needed
  -> Auth request interceptor: add Bearer token (only if request passes through)
  -> Network request (only if online)
  -> Existing 401/error response interceptor
  -> Offline response interceptor: cache GET responses / handle offline signals
  -> Page receives response.data (same shape whether from network or cache)
```

### GET Requests (Reads)
- **Stale-while-revalidate when online**: If cached data exists, the app returns it immediately and fires a background network request. When the background request succeeds, the cache is updated silently and a brief "Updated" indicator appears. This ensures instant page loads on slow connections.
- **Cache fallback when offline**: When fully offline, cached data is served directly from IndexedDB with no network attempt.
- Data is keyed by `METHOD:path?query` (e.g. `GET:/hubs/3/batteries`).

### POST/PUT/DELETE Requests (Mutations)
- **Queue when offline**: Mutations are stored in an IndexedDB queue with method, URL, and payload. The page receives a synthetic success response (HTTP 202) so it behaves normally.
- **Process FIFO when online**: The sync manager replays queued mutations sequentially, re-injecting a fresh auth token at sync time.

### Service Worker
- Workbox `generateSW` mode with `runtimeCaching` rules as a belt-and-suspenders backup:
  - `NetworkFirst` for API routes (1hr max, 5s network timeout)
  - `CacheFirst` for static assets like images and fonts (1 week max)

## Cache Warming (Pre-fetch)

The app proactively pre-fetches all key API endpoints so that data is available offline before the user navigates to each page. This runs automatically in the background at three trigger points:

1. **After login**: Immediately after successful authentication, all list endpoints, settings, and individual detail pages are fetched and cached.
2. **On app startup**: If the user is already authenticated (token in localStorage), the cache is refreshed in the background.
3. **When connectivity returns**: When the device comes back online, the cache is re-warmed alongside the mutation sync.

The warmer fetches in two phases:
- **Phase 1**: All list and settings endpoints for the user's hub (hubs, batteries, users, PUE, rentals, notifications, settings, job cards, etc.) with 3 concurrent requests.
- **Phase 2**: Individual detail pages for each item found in the list responses (up to 50 per resource type).

A 5-minute cooldown prevents re-warming too frequently (e.g. if the device flickers between online/offline).

## Entity Chaining (Offline Workflows)

The system supports chaining related operations while fully offline. For example, you can register a new customer and immediately rent them a battery — all without connectivity. This is achieved through:

1. **Temporary IDs**: Offline-created entities receive negative integer IDs (-1, -2, -3...) that are unique within the session.
2. **Optimistic cache updates**: New entities are immediately merged into the relevant cached lists so they appear in dropdowns and tables. Battery/PUE status updates (available/rented) are reflected instantly in cache.
3. **Temp ID substitution at sync time**: When the mutation queue is processed, the sync manager replaces temp IDs with the real server-assigned IDs. If creating user -1 returns `user_id: 42`, subsequent queued mutations referencing -1 (in URL paths and JSON bodies) are rewritten to use 42 before sending.

### Supported Offline Workflows

| Workflow | What happens offline |
|----------|---------------------|
| Register user, then rent battery to them | User gets temp ID, appears in rental form's user dropdown. Rental queued with temp user_id; substituted at sync. |
| Return battery, then rent to someone else | Battery status flipped to "available" in cache, immediately available for new rental. |
| Return battery, complete survey | Return queued, survey submission queued (references rental_id). |
| Create battery, then rent it out | Battery gets temp ID, appears in battery list. Rental references temp battery_id. |
| Register PUE, then rent it | PUE gets temp ID, rental references temp pue_id. |

### Optimistic Updates by Resource

| Resource | On Create | On Return |
|----------|-----------|-----------|
| User | Synthetic user added to all user list caches (global + hub-specific) | N/A |
| Battery | Synthetic battery added to battery list caches | Battery status set to "available" |
| Battery Rental | Batteries marked "rented" in cache; synthetic rental added to rental lists | Batteries marked "available"; rental marked "returned" |
| PUE | Synthetic PUE added to PUE list caches | N/A |
| PUE Rental | PUE marked "rented" in cache; synthetic rental added | PUE marked "available"; rental marked "returned" |
| Cost Structure | Synthetic structure added to cost-structures list cache | N/A |

## Files

| File | Purpose |
|------|---------|
| `frontend/src/services/offlineDb.js` | IndexedDB persistence layer (cache store, mutation queue, sync metadata, temp IDs, optimistic cache mutations) |
| `frontend/src/services/offlineInterceptor.js` | Axios request/response interceptors for offline caching and mutation queuing |
| `frontend/src/services/offlineOptimistic.js` | Optimistic cache updates and synthetic response generation for offline mutations |
| `frontend/src/services/syncManager.js` | Background sync orchestration (queue processing, cache invalidation, temp ID substitution, periodic retry) |
| `frontend/src/services/cacheWarmer.js` | Pre-fetches all API endpoints to populate cache for offline use |
| `frontend/src/boot/offline.js` | Boot file that wires IndexedDB, interceptors, sync manager, and cache warmer together |

## UI Indicators

Four indicator chips can appear in the top toolbar (MainLayout.vue):

- **Orange "Offline" chip** with cloud_off icon: shown when `navigator.onLine` is false
- **Blue "Syncing N" chip** with spinning sync icon: shown when online with N pending mutations in the queue
- **Red "N Failed" chip** with error icon: shown when failed mutations exist. Click to open a dialog listing each failed mutation with Retry and Discard buttons.
- **Teal "Updated" chip** with check icon: briefly shown (2 seconds) when background revalidation refreshes cached data

## TTL Cache Strategy

| URL Pattern | TTL |
|-------------|-----|
| `/settings/` | 60 minutes |
| `/hubs/` | 30 minutes |
| `/users/` | 15 minutes |
| `/batteries/`, `/pue/` | 5 minutes |
| `/rentals/`, `/battery-rentals/`, `/pue-rentals/` | 2 minutes |
| `/data/` (telemetry) | 1 minute |
| Everything else | 5 minutes (default) |

## Excluded Endpoints

These endpoints are never cached or queued offline:
- `/auth/token` and `/auth/battery-*` (authentication)
- `/health` (health check)
- `/analytics/export/` (CSV blob downloads)
- `/return-survey/responses/export` (CSV blob downloads)
- Any request with `responseType: 'blob'`

## Sync Behaviour

- When the browser fires an `online` event, sync triggers after a 2-second debounce
- A periodic 30-second timer retries if there are pending mutations
- Expired cache entries are cleaned every 10 minutes
- A `syncInProgress` flag in IndexedDB prevents concurrent syncs across browser tabs (with a 60-second deadlock timeout)

### Sync Error Handling

| Error | Behaviour |
|-------|-----------|
| 401 Unauthorized | Stop sync, surface "session expired" |
| 4xx Client Error | Mark mutation as failed, continue with next |
| 5xx Server Error | Increment retry counter, stop and retry later (max 5 retries) |
| Network Error | Stop sync, retry on next timer tick |

## How IndexedDB Works with PWA Install

When a user "installs" the PWA (adds to home screen), the IndexedDB database is created on first app load. The cache warmer then pre-fetches all key endpoints in the background, so the user doesn't need to visit every page first. The database persists in the browser's storage and survives app restarts, device reboots, and offline periods. It is scoped to the app's origin and is not shared with other sites.

The database (`beppp-offline`) contains three object stores:
- `apiCache`: Cached API responses keyed by request method + URL
- `mutationQueue`: Queued offline mutations (auto-incrementing ID, FIFO processing)
- `syncMeta`: Key-value pairs for sync state tracking (e.g. lock timestamps)

## Development

```bash
# Install dependencies (includes idb library)
make frontend-install

# Build the PWA
make frontend-build

# Test offline behaviour:
# 1. Serve the built PWA and open in Chrome
# 2. Log in -- cache warmer pre-fetches all endpoints in background
# 3. DevTools > Application > IndexedDB > beppp-offline > apiCache -- verify entries appearing
# 4. Wait ~30s for cache warming to complete
# 5. Chrome DevTools > Network > Offline checkbox
# 6. Navigate pages -- should show cached data with orange "Offline" chip
# 7. Create a record -- should appear to succeed, blue "Syncing 1" chip visible
# 8. Uncheck Offline -- sync processes automatically, cache re-warms
# 9. DevTools > Application > IndexedDB > beppp-offline to inspect stores
```
