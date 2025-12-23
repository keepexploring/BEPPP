import { date } from 'quasar'
import { useHubSettingsStore } from 'stores/hubSettings'

/**
 * Format a date string with timezone from hub settings
 * @param {string|Date} dateStr - Date to format
 * @param {string} format - Format string (Quasar date format)
 * @returns {string} Formatted date with timezone
 */
export function formatDateWithTimezone(dateStr, format = 'MMM DD, YYYY HH:mm:ss') {
  if (!dateStr) return '-'

  const hubSettingsStore = useHubSettingsStore()
  const timezone = hubSettingsStore.currentTimezone || 'UTC'

  return date.formatDate(dateStr, format) + ` ${timezone}`
}

/**
 * Format a date using toLocaleString with timezone
 * @param {string|Date} dateStr - Date to format
 * @returns {string} Formatted date with timezone
 */
export function formatLocaleDateWithTimezone(dateStr) {
  if (!dateStr) return ''

  const hubSettingsStore = useHubSettingsStore()
  const timezone = hubSettingsStore.currentTimezone || 'UTC'

  return new Date(dateStr).toLocaleString() + ` ${timezone}`
}
