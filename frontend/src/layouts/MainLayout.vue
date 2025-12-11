<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer" />

        <q-toolbar-title>
          <q-icon name="battery_charging_full" size="sm" />
          Battery Hub Manager
        </q-toolbar-title>

        <q-space />

        <q-btn flat round dense icon="notifications">
          <q-badge v-if="unreadCount > 0" color="red" floating>{{ unreadCount }}</q-badge>
          <q-menu max-width="400px">
            <q-list style="min-width: 350px; max-height: 400px">
              <q-item>
                <q-item-section>
                  <q-item-label class="text-weight-bold">Notifications</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat dense size="sm" label="Mark all read" @click="markAllAsRead" v-if="unreadCount > 0" />
                </q-item-section>
              </q-item>
              <q-separator />

              <div v-if="notifications.length === 0" class="q-pa-md text-center text-grey-6">
                No notifications
              </div>

              <q-item
                v-for="notification in notifications"
                :key="notification.id"
                clickable
                :class="{ 'bg-blue-1': !notification.read }"
                @click="handleNotificationClick(notification)"
              >
                <q-item-section avatar>
                  <q-avatar :color="getNotificationColor(notification.severity)" text-color="white" :icon="getNotificationIcon(notification.type)" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ notification.title }}</q-item-label>
                  <q-item-label caption lines="2">{{ notification.message }}</q-item-label>
                  <q-item-label caption class="text-grey-6">{{ formatTimestamp(notification.timestamp) }}</q-item-label>
                </q-item-section>
                <q-item-section side v-if="!notification.read">
                  <q-icon name="circle" color="primary" size="8px" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>

        <q-btn flat round dense icon="account_circle">
          <q-menu>
            <q-list style="min-width: 200px">
              <q-item>
                <q-item-section>
                  <q-item-label>{{ authStore.userName }}</q-item-label>
                  <q-item-label caption>{{ authStore.role }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-item clickable v-close-popup @click="handleLogout">
                <q-item-section avatar>
                  <q-icon name="logout" />
                </q-item-section>
                <q-item-section>Logout</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item-label header>Navigation</q-item-label>

        <q-item
          clickable
          :to="{ name: 'dashboard' }"
          exact
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Dashboard</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          :to="{ name: 'analytics' }"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="analytics" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Analytics</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator />

        <q-item-label header>Management</q-item-label>

        <q-item
          clickable
          :to="{ name: 'hubs' }"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="hub" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Hubs</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          :to="{ name: 'batteries' }"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="battery_charging_full" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Batteries</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          :to="{ name: 'pue' }"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="devices" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Equipment (PUE)</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          :to="{ name: 'rentals' }"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="receipt" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Rentals</q-item-label>
          </q-item-section>
        </q-item>

        <template v-if="authStore.isAdmin">
          <q-separator />

          <q-item-label header>Administration</q-item-label>

          <q-item
            clickable
            :to="{ name: 'users' }"
            v-ripple
          >
            <q-item-section avatar>
              <q-icon name="people" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Users</q-item-label>
            </q-item-section>
          </q-item>

          <q-item
            clickable
            :to="{ name: 'settings' }"
            v-ripple
          >
            <q-item-section avatar>
              <q-icon name="settings" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Settings</q-item-label>
            </q-item-section>
          </q-item>

          <q-item
            clickable
            :to="{ name: 'accounts' }"
            v-ripple
          >
            <q-item-section avatar>
              <q-icon name="account_balance" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Accounts</q-item-label>
            </q-item-section>
          </q-item>

          <q-item
            clickable
            :to="{ name: 'webhook-logs' }"
            v-ripple
          >
            <q-item-section avatar>
              <q-icon name="webhook" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Webhook Logs</q-item-label>
            </q-item-section>
          </q-item>
        </template>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'
import { notificationsAPI } from 'src/services/api'

const authStore = useAuthStore()
const router = useRouter()
const leftDrawerOpen = ref(false)

// Notifications
const notifications = ref([])

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

const loadNotifications = async () => {
  try {
    const hubId = authStore.user?.hub_id
    if (!hubId) return

    const response = await notificationsAPI.getNotifications({ hub_id: hubId })
    notifications.value = response.data.notifications || []
  } catch (error) {
    console.error('Failed to load notifications:', error)
  }
}

const triggerNotificationCheck = async () => {
  try {
    const hubId = authStore.user?.hub_id
    if (!hubId) return

    await notificationsAPI.triggerNotificationCheck({ hub_id: hubId })
    await loadNotifications()
  } catch (error) {
    console.error('Failed to check notifications:', error)
  }
}

const getNotificationIcon = (type) => {
  const icons = {
    'overdue_rental': 'warning',
    'debt_threshold': 'error',
    'low_battery': 'battery_alert',
    'warning': 'warning',
    'error': 'error',
    'info': 'info',
    'success': 'check_circle'
  }
  return icons[type] || 'notifications'
}

const getNotificationColor = (severity) => {
  const colors = {
    'warning': 'orange',
    'error': 'red',
    'info': 'blue',
    'success': 'green'
  }
  return colors[severity] || 'grey'
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

const handleNotificationClick = async (notification) => {
  // Mark as read in backend
  try {
    await notificationsAPI.markAsRead(notification.id)
    notification.read = true

    // Navigate based on link type
    if (notification.link_type && notification.link_id) {
      const routes = {
        'rental': { name: 'rentals' },
        'user': { name: 'user-detail', params: { id: notification.link_id } },
        'battery': { name: 'batteries' },
        'account': { name: 'accounts' }
      }

      const route = routes[notification.link_type]
      if (route) {
        router.push(route)
      }
    }
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
  }
}

const markAllAsRead = async () => {
  try {
    const hubId = authStore.user?.hub_id
    if (!hubId) return

    await notificationsAPI.markAllAsRead({ hub_id: hubId })
    notifications.value.forEach(n => n.read = true)
  } catch (error) {
    console.error('Failed to mark all as read:', error)
  }
}

const toggleLeftDrawer = () => {
  leftDrawerOpen.value = !leftDrawerOpen.value
}

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}

// Trigger notification check and load on mount
onMounted(() => {
  triggerNotificationCheck()
})
</script>
