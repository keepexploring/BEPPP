import { ref, computed } from 'vue'
import { useAuthStore } from 'stores/auth'
import { settingsAPI } from 'src/services/api'

// Global hub settings cache
const hubSettingsCache = ref({})
const loadingSettings = ref(false)

/**
 * Composable for currency management across the application
 * Ensures consistent currency display based on hub settings
 */
export function useCurrency() {
  const authStore = useAuthStore()

  /**
   * Get currency symbol from currency code
   */
  const getCurrencySymbol = (currency) => {
    const symbols = {
      'USD': '$',
      'GBP': '£',
      'EUR': '€',
      'MWK': 'MK',
      'ZAR': 'R',
      'KES': 'KSh',
      'UGX': 'USh',
      'TZS': 'TSh'
    }
    return symbols[currency] || currency
  }

  /**
   * Load hub settings for a specific hub
   */
  const loadHubSettings = async (hubId) => {
    if (!hubId) return null

    // Return cached settings if available
    if (hubSettingsCache.value[hubId]) {
      return hubSettingsCache.value[hubId]
    }

    // Load from API
    if (!loadingSettings.value) {
      try {
        loadingSettings.value = true
        const response = await settingsAPI.getHubSettings(hubId)
        hubSettingsCache.value[hubId] = response.data
        return response.data
      } catch (error) {
        console.error('Failed to load hub settings:', error)
        return null
      } finally {
        loadingSettings.value = false
      }
    }

    return null
  }

  /**
   * Get hub settings for the current user or specified hub
   */
  const getHubSettings = async (hubId = null) => {
    const targetHubId = hubId || authStore.user?.hub_id
    if (!targetHubId) return null
    return await loadHubSettings(targetHubId)
  }

  /**
   * Get currency for a specific hub
   */
  const getHubCurrency = async (hubId = null) => {
    const settings = await getHubSettings(hubId)
    return settings?.default_currency || 'USD'
  }

  /**
   * Get currency symbol for a specific hub
   */
  const getHubCurrencySymbol = async (hubId = null) => {
    const currency = await getHubCurrency(hubId)
    return getCurrencySymbol(currency)
  }

  /**
   * Computed property for current user's hub currency
   */
  const currentCurrency = computed(() => {
    const hubId = authStore.user?.hub_id
    if (!hubId || !hubSettingsCache.value[hubId]) return 'USD'
    return hubSettingsCache.value[hubId]?.default_currency || 'USD'
  })

  /**
   * Computed property for current user's hub currency symbol
   */
  const currentCurrencySymbol = computed(() => {
    return getCurrencySymbol(currentCurrency.value)
  })

  /**
   * Format amount with currency symbol
   */
  const formatCurrency = (amount, hubId = null, showSymbol = true) => {
    const settings = hubId ? hubSettingsCache.value[hubId] : null
    const currency = settings?.default_currency || currentCurrency.value
    const symbol = getCurrencySymbol(currency)

    const formattedAmount = typeof amount === 'number'
      ? amount.toFixed(2)
      : parseFloat(amount || 0).toFixed(2)

    return showSymbol ? `${symbol}${formattedAmount}` : formattedAmount
  }

  /**
   * Clear cache (useful when settings are updated)
   */
  const clearCache = () => {
    hubSettingsCache.value = {}
  }

  /**
   * Initialize currency settings for current user
   */
  const initializeCurrency = async () => {
    const hubId = authStore.user?.hub_id
    if (hubId) {
      await loadHubSettings(hubId)
    }
  }

  return {
    getCurrencySymbol,
    getHubCurrency,
    getHubCurrencySymbol,
    currentCurrency,
    currentCurrencySymbol,
    formatCurrency,
    loadHubSettings,
    getHubSettings,
    clearCache,
    initializeCurrency
  }
}
