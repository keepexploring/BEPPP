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
      Notify.create({
        type: 'negative',
        message: error.response.data.detail,
        position: 'top'
      })
    }
    return Promise.reject(error)
  }
)

// Authentication
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/token', new URLSearchParams({ username, password })),
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
  get: (batteryId) => api.get(`/batteries/${batteryId}`),
  getByShortId: (shortId) => api.get(`/batteries/by-short-id/${shortId}`),
  create: (data) => api.post('/batteries/', data),
  update: (batteryId, data) => api.put(`/batteries/${batteryId}`, data),
  delete: (batteryId) => api.delete(`/batteries/${batteryId}`),
  setBatterySecret: (batteryId, secret) =>
    api.post(`/admin/battery-secret/${batteryId}`, { secret })
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
  get: (rentalId) => api.get(`/rentals/${rentalId}`),
  create: (data) => api.post('/rentals/', data),
  update: (rentalId, data) => api.put(`/rentals/${rentalId}`, data),
  delete: (rentalId) => api.delete(`/rentals/${rentalId}`),
  returnBattery: (rentalId, data) =>
    api.post(`/rentals/${rentalId}/return`, data),
  addPUE: (rentalId, pueId) =>
    api.post(`/rentals/${rentalId}/add-pue`, { pue_id: pueId }),
  returnPUE: (rentalId, pueId, data) =>
    api.put(`/rentals/${rentalId}/pue-items/${pueId}/return`, data)
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

export default api
