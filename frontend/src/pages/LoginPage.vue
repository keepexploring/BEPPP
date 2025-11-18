<template>
  <q-layout>
    <q-page-container>
      <q-page class="flex flex-center bg-gradient">
        <q-card class="login-card">
          <q-card-section class="text-center">
            <q-icon name="battery_charging_full" size="64px" color="primary" />
            <div class="text-h5 q-mt-sm">Battery Hub Manager</div>
            <div class="text-subtitle2 text-grey-7">Sign in to continue</div>
          </q-card-section>

          <q-card-section>
            <q-form @submit="handleLogin" class="q-gutter-md">
              <q-input
                v-model="username"
                label="Username"
                outlined
                :rules="[val => !!val || 'Username is required']"
                autofocus
              >
                <template v-slot:prepend>
                  <q-icon name="person" />
                </template>
              </q-input>

              <q-input
                v-model="password"
                label="Password"
                type="password"
                outlined
                :rules="[val => !!val || 'Password is required']"
              >
                <template v-slot:prepend>
                  <q-icon name="lock" />
                </template>
              </q-input>

              <q-btn
                label="Sign In"
                type="submit"
                color="primary"
                class="full-width"
                :loading="loading"
                size="lg"
              />
            </q-form>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true

  try {
    const result = await authStore.login(username.value, password.value)

    if (result.success) {
      $q.notify({
        type: 'positive',
        message: 'Login successful!',
        position: 'top'
      })

      const redirect = route.query.redirect || '/'
      router.push(redirect)
    } else {
      $q.notify({
        type: 'negative',
        message: result.error || 'Invalid credentials',
        position: 'top'
      })
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Login failed. Please try again.',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.bg-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  min-width: 400px;
  max-width: 90vw;
}
</style>
