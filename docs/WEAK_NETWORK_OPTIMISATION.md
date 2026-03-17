# Weak Network Optimisation Ideas

Collected ideas for improving app performance on weak/intermittent networks (2G, 3G, spotty WiFi). The app already has a full offline-first PWA system with stale-while-revalidate caching - these are additional improvements.

## Current State (What Already Works)

- **Stale-while-revalidate**: Pages load instantly from IndexedDB cache, revalidate in background
- **Full offline mode**: All CRUD operations work offline, queued mutations sync when connectivity returns
- **401 guard**: Network errors don't accidentally log users out
- **Automatic retry**: Failed syncs retry up to 5 times with 30s periodic sync attempts
- **PWA service worker**: Static assets cached for instant page loads

## Proposed Improvements

### 1. GZip/Brotli Compression
- **Impact**: High - can reduce JSON payload sizes by 70-90%
- **Effort**: Low
- Add `GZipMiddleware` from `starlette.middleware.gzip` to FastAPI
- Check if nginx in production already handles this (may just need backend for dev)
- Particularly beneficial for large list endpoints (users, batteries, rentals)

### 2. Request Timeout Tuning
- **Impact**: Medium - prevents UI hanging on weak connections
- **Effort**: Low
- Set explicit axios timeouts: ~10s for GETs, ~30s for mutations
- Faster fallback to cached data instead of waiting indefinitely
- Currently no explicit timeout is set on the axios instance

### 3. Lazy Loading / Pagination
- **Impact**: High - reduces initial data transfer
- **Effort**: Medium
- Large list endpoints (users, batteries, rentals) could paginate
- Only fetch data needed for the current view
- Reduces initial payload size significantly on weak networks

### 4. Background Sync API (Service Worker)
- **Impact**: Medium - more reliable mutation delivery
- **Effort**: Medium
- Use the native Service Worker Background Sync API
- Mutations sync even if the user closes the browser tab
- Currently using custom JS timer sync (only works while app is open)

### 5. Connection Quality Detection
- **Impact**: Medium - adapts behavior to network conditions
- **Effort**: Medium
- Use `navigator.connection` (Network Information API) to detect 2G/3G/4G
- Skip background revalidation on very slow connections (2G)
- Show connection quality indicator to users
- Reduce image quality on slow connections

### 6. Offline Login
- **Impact**: High - removes biggest offline blocker
- **Effort**: Medium
- Cache hashed credentials + user profile after first successful login
- Validate locally when offline, use cached JWT token
- Re-authenticate silently when connectivity returns
- Currently login requires network connectivity

### 7. Response Caching Headers
- **Impact**: Low-Medium
- **Effort**: Low
- Set appropriate `Cache-Control` headers on API responses
- Service worker can use these for smarter caching decisions
- Helps browser and proxy caches along the way

### 8. Delta/Incremental Sync
- **Impact**: Very High - dramatically reduces data transfer
- **Effort**: High
- Instead of fetching full lists, fetch only changes since last sync
- Requires backend support (`modified_after` parameter on list endpoints)
- Would need `updated_at` timestamps on all models
- Huge win for subsequent loads after initial cache warm
