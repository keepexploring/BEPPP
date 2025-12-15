import axios from 'axios'
import { useAuthStore } from 'stores/auth'
import { Notify } from 'quasar'

const api = axios.create({
  baseURL: process.env.API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      Notify.create({
        type: 'negative',
        message: 'Session expired. Please login again.',
        position: 'top'
      })
    } else if (error.response?.data?.detail) {
      // Ensure detail is a string, not an object
      const detail = error.response.data.detail
      const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      Notify.create({
        type: 'negative',
        message: message,
        position: 'top'
      })
    }
    return Promise.reject(error)
  }
)

// Authentication
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/token', { username, password }),
  batteryLogin: (battery_id, secret) =>
    api.post('/auth/battery-login', { battery_id, secret }),
  batteryRefresh: (refreshToken) =>
    api.post('/auth/battery-refresh', { refresh_token: refreshToken }),
  getTokenConfig: () =>
    api.get('/admin/token-config')
}

// Hubs
export const hubsAPI = {
  list: () => api.get('/hubs/'),
  get: (hubId) => api.get(`/hubs/${hubId}`),
  create: (data) => api.post('/hubs/', data),
  update: (hubId, data) => api.put(`/hubs/${hubId}`, data),
  delete: (hubId) => api.delete(`/hubs/${hubId}`),
  getUsers: (hubId) => api.get(`/hubs/${hubId}/users`),
  getBatteries: (hubId) => api.get(`/hubs/${hubId}/batteries`),
  getPUE: (hubId) => api.get(`/hubs/${hubId}/pue`),
  getAvailablePUE: (hubId) => api.get(`/hubs/${hubId}/pue/available`)
}

// Users
export const usersAPI = {
  get: (userId) => api.get(`/users/${userId}`),
  getByShortId: (shortId) => api.get(`/users/by-short-id/${shortId}`),
  create: (data) => api.post('/users/', data),
  update: (userId, data) => api.put(`/users/${userId}`, data),
  delete: (userId) => api.delete(`/users/${userId}`),
  grantHubAccess: (userId, hubId) =>
    api.post(`/admin/user-hub-access/${userId}/${hubId}`),
  revokeHubAccess: (userId, hubId) =>
    api.delete(`/admin/user-hub-access/${userId}/${hubId}`)
}

// Batteries
export const batteriesAPI = {
  list: (params) => api.get('/batteries/', { params }),
  get: (batteryId) => api.get(`/batteries/${batteryId}`),
  getByShortId: (shortId) => api.get(`/batteries/by-short-id/${shortId}`),
  create: (data) => api.post('/batteries/', data),
  update: (batteryId, data) => api.put(`/batteries/${batteryId}`, data),
  delete: (batteryId) => api.delete(`/batteries/${batteryId}`),
  setBatterySecret: (batteryId, newSecret) =>
    api.post(`/admin/battery-secret/${batteryId}`, { new_secret: newSecret }),
  getNotes: (batteryId) => api.get(`/batteries/${batteryId}/notes`),
  createNote: (batteryId, data) => api.post(`/batteries/${batteryId}/notes`, data),
  getErrors: (batteryId, timePeriod = 'last_week', limit = 50) =>
    api.get(`/batteries/${batteryId}/errors`, { params: { time_period: timePeriod, limit } })
}

// PUE (Productive Use Equipment)
export const pueAPI = {
  get: (pueId) => api.get(`/pue/${pueId}`),
  create: (data) => api.post('/pue/', data),
  update: (pueId, data) => api.put(`/pue/${pueId}`, data),
  delete: (pueId) => api.delete(`/pue/${pueId}`)
}

// Rentals
export const rentalsAPI = {
  list: (params) => api.get('/rentals/', { params }),
  get: (rentalId) => api.get(`/rentals/${rentalId}`),
  getOverdueUpcoming: () => api.get('/rentals/overdue-upcoming'),
  create: (data) => api.post('/rentals/', data),
  update: (rentalId, data) => api.put(`/rentals/${rentalId}`, data),
  delete: (rentalId) => api.delete(`/rentals/${rentalId}`),
  returnBattery: (rentalId, data) =>
    api.post(`/rentals/${rentalId}/return`, data),
  addPUE: (rentalId, pueId) =>
    api.post(`/rentals/${rentalId}/add-pue`, { pue_id: pueId }),
  returnPUE: (rentalId, pueId, data) =>
    api.put(`/rentals/${rentalId}/pue-items/${pueId}/return`, data),
  calculateReturnCost: (rentalId, params) =>
    api.get(`/rentals/${rentalId}/calculate-return-cost`, { params })
}

// Data
export const dataAPI = {
  getBatteryData: (batteryId, params) =>
    api.get(`/data/battery/${batteryId}`, { params }),
  getLatest: (batteryId) =>
    api.get(`/data/latest/${batteryId}`)
}

// Analytics
export const analyticsAPI = {
  hubSummary: (params) =>
    api.get('/analytics/hub-summary', { params }),
  powerUsage: (data) =>
    api.post('/analytics/power-usage', data),
  batteryPerformance: (params) =>
    api.get('/analytics/battery-performance', { params }),
  rentalStatistics: (data) =>
    api.post('/analytics/rental-statistics', data),
  revenue: (params) =>
    api.get('/analytics/revenue', { params }),
  deviceUtilization: (hubId, params) =>
    api.get(`/analytics/device-utilization/${hubId}`, { params }),
  exportData: (hubId, params) =>
    api.get(`/analytics/export/${hubId}`, { params })
}

// Admin
export const adminAPI = {
  getWebhookLogs: (params) =>
    api.get('/admin/webhook-logs', { params })
}

// Health
export const healthAPI = {
  check: () => api.get('/health')
}

// Settings
export const settingsAPI = {
  // Duration Presets
  getDurationPresets: (hubId) =>
    api.get('/settings/rental-durations', { params: { hub_id: hubId } }),
  createDurationPreset: (data) =>
    api.post('/settings/rental-durations', null, { params: data }),
  updateDurationPreset: (presetId, data) =>
    api.put(`/settings/rental-durations/${presetId}`, null, { params: data }),
  deleteDurationPreset: (presetId) =>
    api.delete(`/settings/rental-durations/${presetId}`),

  // PUE Types
  getPUETypes: (hubId) =>
    api.get('/settings/pue-types', { params: { hub_id: hubId } }),
  createPUEType: (data) =>
    api.post('/settings/pue-types', null, { params: data }),
  updatePUEType: (typeId, data) =>
    api.put(`/settings/pue-types/${typeId}`, null, { params: data }),
  deletePUEType: (typeId) =>
    api.delete(`/settings/pue-types/${typeId}`),

  // Pricing
  getPricingConfigs: (params) =>
    api.get('/settings/pricing', { params }),
  createPricingConfig: (data) =>
    api.post('/settings/pricing', null, { params: data }),
  updatePricingConfig: (pricingId, data) =>
    api.put(`/settings/pricing/${pricingId}`, null, { params: data }),
  deletePricingConfig: (pricingId) =>
    api.delete(`/settings/pricing/${pricingId}`),

  // Deposit Presets
  getDepositPresets: (params) =>
    api.get('/settings/deposit-presets', { params }),
  createDepositPreset: (data) =>
    api.post('/settings/deposit-presets', null, { params: data }),
  deleteDepositPreset: (presetId) =>
    api.delete(`/settings/deposit-presets/${presetId}`),

  // Payment Types
  getPaymentTypes: (params) =>
    api.get('/settings/payment-types', { params }),
  createPaymentType: (data) =>
    api.post('/settings/payment-types', null, { params: data }),
  deletePaymentType: (typeId) =>
    api.delete(`/settings/payment-types/${typeId}`),

  // Hub Settings
  getHubSettings: (hubId) =>
    api.get(`/settings/hub/${hubId}`),
  updateHubSettings: (hubId, data) =>
    api.put(`/settings/hub/${hubId}`, null, { params: data }),

  // Cost Structures
  getCostStructures: (params) =>
    api.get('/settings/cost-structures', { params }),
  createCostStructure: (data) =>
    api.post('/settings/cost-structures', null, { params: data }),
  updateCostStructure: (structureId, data) =>
    api.put(`/settings/cost-structures/${structureId}`, null, { params: data }),
  deleteCostStructure: (structureId) =>
    api.delete(`/settings/cost-structures/${structureId}`),
  estimateCost: (structureId, params) =>
    api.post(`/settings/cost-structures/${structureId}/estimate`, null, { params }),

  // Subscription Packages
  getSubscriptionPackages: (hubId, includeInactive = false) =>
    api.get('/settings/subscription-packages', { params: { hub_id: hubId, include_inactive: includeInactive } }),
  createSubscriptionPackage: (data) =>
    api.post('/settings/subscription-packages', null, { params: data }),
  updateSubscriptionPackage: (packageId, data) =>
    api.put(`/settings/subscription-packages/${packageId}`, null, { params: data }),
  deleteSubscriptionPackage: (packageId) =>
    api.delete(`/settings/subscription-packages/${packageId}`)
}

// User Subscriptions
export const subscriptionsAPI = {
  getUserSubscriptions: (userId) =>
    api.get(`/users/${userId}/subscriptions`),
  assignSubscription: (userId, data) =>
    api.post(`/users/${userId}/subscriptions`, null, { params: data }),
  updateUserSubscription: (userId, subscriptionId, data) =>
    api.put(`/users/${userId}/subscriptions/${subscriptionId}`, data),
  cancelUserSubscription: (userId, subscriptionId) =>
    api.delete(`/users/${userId}/subscriptions/${subscriptionId}`)
}

// Accounts
export const accountsAPI = {
  // User Accounts
  getUserAccount: (userId) =>
    api.get(`/accounts/user/${userId}`),
  createTransaction: (userId, data) =>
    api.post(`/accounts/user/${userId}/transaction`, null, { params: data }),
  getUserTransactions: (userId, params) =>
    api.get(`/accounts/user/${userId}/transactions`, { params }),

  // Hub Accounts
  getHubSummary: (hubId, params) =>
    api.get(`/accounts/hub/${hubId}/summary`, { params }),
  getUsersInDebt: (params) =>
    api.get('/accounts/users/in-debt', { params })
}

// Notifications
export const notificationsAPI = {
  getNotifications: (params) =>
    api.get('/notifications', { params }),
  create: (data) =>
    api.post('/notifications', data),
  triggerNotificationCheck: (params) =>
    api.post('/notifications/check', null, { params }),
  markAsRead: (notificationId) =>
    api.put(`/notifications/${notificationId}/read`),
  markAllAsRead: (params) =>
    api.put('/notifications/mark-all-read', null, { params })
}

export default api
