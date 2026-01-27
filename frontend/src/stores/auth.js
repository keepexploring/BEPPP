import { defineStore } from 'pinia'
import { authAPI } from 'src/services/api'
import { LocalStorage } from 'quasar'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: LocalStorage.getItem('token') || null,
    user: LocalStorage.getItem('user') || null,
    role: LocalStorage.getItem('role') || null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => ['admin', 'superadmin'].includes(state.role),
    isSuperAdmin: (state) => state.role === 'superadmin',
    isDataAdmin: (state) => state.role === 'data_admin',
    userName: (state) => state.user?.username || 'User',
    currentHubId: (state) => state.user?.hub_id || null
  },

  actions: {
    async login(username, password) {
      try {
        const response = await authAPI.login(username, password)
        const { access_token, user_id, role, hub_id } = response.data

        this.token = access_token
        this.user = { username, user_id, hub_id }
        this.role = role

        LocalStorage.set('token', access_token)
        LocalStorage.set('user', this.user)
        LocalStorage.set('role', role)

        return { success: true }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.detail || 'Login failed'
        }
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.role = null

      LocalStorage.remove('token')
      LocalStorage.remove('user')
      LocalStorage.remove('role')
    },

    updateUser(userData) {
      this.user = { ...this.user, ...userData }
      LocalStorage.set('user', this.user)
    }
  }
})
