import { defineStore } from 'pinia'
import { settingsAPI } from 'src/services/api'
import { useAuthStore } from './auth'

export const useHubSettingsStore = defineStore('hubSettings', {
  state: () => ({
    settings: {}, // Keyed by hub_id
    loading: false
  }),

  getters: {
    /**
     * Get settings for current user's hub
     */
    currentHubSettings: (state) => {
      const authStore = useAuthStore()
      const hubId = authStore.user?.hub_id
      return hubId ? state.settings[hubId] : null
    },

    /**
     * Get currency for current user's hub
     */
    currentCurrency: (state) => {
      const authStore = useAuthStore()
      const hubId = authStore.user?.hub_id
      return hubId && state.settings[hubId]
        ? state.settings[hubId].default_currency
        : 'USD'
    },

    /**
     * Get currency symbol for current user's hub
     */
    currentCurrencySymbol() {
      const authStore = useAuthStore()
      const hubId = authStore.user?.hub_id
      // Use custom symbol if set, otherwise use default mapping
      if (hubId && this.settings[hubId]?.currency_symbol) {
        return this.settings[hubId].currency_symbol
      }
      return this.getCurrencySymbol(this.currentCurrency)
    },

    /**
     * Get pagination setting for current user's hub
     */
    currentTableRowsPerPage: (state) => {
      const authStore = useAuthStore()
      const hubId = authStore.user?.hub_id
      return hubId && state.settings[hubId]
        ? state.settings[hubId].default_table_rows_per_page || 50
        : 50
    }
  },

  actions: {
    /**
     * Load hub settings from API
     */
    async loadHubSettings(hubId) {
      if (!hubId) return

      // Return cached if available
      if (this.settings[hubId]) {
        return this.settings[hubId]
      }

      try {
        this.loading = true
        const response = await settingsAPI.getHubSettings(hubId)
        this.settings[hubId] = response.data
        return response.data
      } catch (error) {
        console.error('Failed to load hub settings:', error)
        // Set default settings on error
        this.settings[hubId] = {
          default_currency: 'USD',
          default_table_rows_per_page: 50,
          debt_notification_threshold: -100,
          overdue_notification_hours: 24,
          vat_percentage: 0,
          timezone: 'UTC'
        }
        return this.settings[hubId]
      } finally {
        this.loading = false
      }
    },

    /**
     * Initialize settings for current user
     */
    async initialize() {
      const authStore = useAuthStore()
      const hubId = authStore.user?.hub_id
      if (hubId) {
        await this.loadHubSettings(hubId)
      }
    },

    /**
     * Get currency symbol from currency code
     */
    getCurrencySymbol(currency) {
      const symbols = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
        'MWK': 'MK',
        'ZAR': 'R',
        'KES': 'KSh',
        'UGX': 'USh',
        'TZS': 'TSh',
        'NGN': '₦',
        'GHS': '₵',
        'RWF': 'RF'
      }
      return symbols[currency] || currency
    },

    /**
     * Get currency for a specific hub
     */
    getHubCurrency(hubId) {
      return this.settings[hubId]?.default_currency || 'USD'
    },

    /**
     * Get currency symbol for a specific hub
     */
    getHubCurrencySymbol(hubId) {
      // Use custom symbol if set
      if (this.settings[hubId]?.currency_symbol) {
        return this.settings[hubId].currency_symbol
      }
      const currency = this.getHubCurrency(hubId)
      return this.getCurrencySymbol(currency)
    },

    /**
     * Format amount with currency
     */
    formatCurrency(amount, hubId = null) {
      const authStore = useAuthStore()
      const targetHubId = hubId || authStore.user?.hub_id
      const currency = this.getHubCurrency(targetHubId)
      const symbol = this.getCurrencySymbol(currency)

      const formattedAmount = typeof amount === 'number'
        ? amount.toFixed(2)
        : parseFloat(amount || 0).toFixed(2)

      return `${symbol}${formattedAmount}`
    },

    /**
     * Update settings (after save in Settings page)
     */
    updateSettings(hubId, newSettings) {
      this.settings[hubId] = { ...this.settings[hubId], ...newSettings }
    },

    /**
     * Clear cache for a hub (useful when settings change)
     */
    clearCache(hubId = null) {
      if (hubId) {
        delete this.settings[hubId]
      } else {
        this.settings = {}
      }
    }
  }
})
