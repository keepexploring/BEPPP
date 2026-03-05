import { useHubSettingsStore } from 'stores/hubSettings'

/**
 * Format a date string with proper timezone conversion using hub settings.
 * Converts UTC dates to the hub's configured timezone.
 * @param {string|Date} dateStr - Date to format (assumed UTC)
 * @param {string} format - 'datetime' (default, with seconds), 'short' (no seconds), or 'date' (date only)
 * @returns {string} Formatted date in hub timezone
 */
export function formatDateWithTimezone(dateStr, format = 'datetime') {
  if (!dateStr) return '-'
  const hubSettingsStore = useHubSettingsStore()
  const tz = hubSettingsStore.currentTimezone || 'UTC'
  const d = new Date(dateStr)
  if (isNaN(d)) return '-'

  const options = { timeZone: tz }
  if (format === 'date') {
    return d.toLocaleDateString('en-GB', { ...options, day: '2-digit', month: 'short', year: 'numeric' })
  }
  if (format === 'short') {
    return d.toLocaleDateString('en-GB', { ...options, day: '2-digit', month: 'short', year: 'numeric' })
      + ' ' + d.toLocaleTimeString('en-GB', { ...options, hour: '2-digit', minute: '2-digit', hour12: false })
  }
  // 'datetime' (default) - full with seconds
  return d.toLocaleDateString('en-GB', { ...options, day: '2-digit', month: 'short', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('en-GB', { ...options, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

/**
 * Get the current timezone label from hub settings
 * @returns {string} Timezone name (e.g. 'Africa/Lagos', 'UTC')
 */
export function getTimezoneLabel() {
  const hubSettingsStore = useHubSettingsStore()
  return hubSettingsStore.currentTimezone || 'UTC'
}
