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
          <q-badge color="red" floating>3</q-badge>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const leftDrawerOpen = ref(false)

const toggleLeftDrawer = () => {
  leftDrawerOpen.value = !leftDrawerOpen.value
}

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>
