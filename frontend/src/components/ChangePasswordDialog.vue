<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" persistent>
    <q-card style="min-width: 500px">
      <q-card-section class="row items-center q-pb-none">
        <q-icon name="vpn_key" color="primary" size="32px" class="q-mr-md" />
        <div class="text-h6">Change Password</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <q-form @submit="handleSubmit" class="q-gutter-md">
          <!-- Current Password -->
          <q-input
            v-model="currentPassword"
            :type="showCurrentPassword ? 'text' : 'password'"
            label="Current Password *"
            outlined
            :rules="[val => !!val || 'Current password is required']"
            autofocus
          >
            <template v-slot:prepend>
              <q-icon name="lock" />
            </template>
            <template v-slot:append>
              <q-btn
                :icon="showCurrentPassword ? 'visibility_off' : 'visibility'"
                flat
                round
                dense
                @click="showCurrentPassword = !showCurrentPassword"
              />
            </template>
          </q-input>

          <!-- New Password -->
          <q-input
            v-model="newPassword"
            :type="showNewPassword ? 'text' : 'password'"
            label="New Password *"
            outlined
            :rules="[val => !!val || 'New password is required', validatePasswordPolicy]"
            hint="Min 8 chars, uppercase, lowercase, digit, special char"
          >
            <template v-slot:prepend>
              <q-icon name="lock_open" />
            </template>
            <template v-slot:append>
              <q-btn
                :icon="showNewPassword ? 'visibility_off' : 'visibility'"
                flat
                round
                dense
                @click="showNewPassword = !showNewPassword"
              />
              <q-btn
                icon="refresh"
                flat
                round
                dense
                @click="generatePassword"
                color="primary"
              >
                <q-tooltip>Generate random password</q-tooltip>
              </q-btn>
            </template>
          </q-input>

          <!-- Password Strength Indicator -->
          <div v-if="newPassword" class="q-mb-md">
            <div class="text-caption q-mb-xs">Password Strength:</div>
            <q-linear-progress
              :value="passwordStrength.value"
              :color="passwordStrength.color"
              size="8px"
              rounded
            />
            <div class="text-caption" :class="`text-${passwordStrength.color}`">
              {{ passwordStrength.label }}
            </div>
          </div>

          <!-- Confirm Password -->
          <q-input
            v-model="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            label="Confirm New Password *"
            outlined
            :rules="[
              val => !!val || 'Please confirm your password',
              val => val === newPassword || 'Passwords do not match'
            ]"
          >
            <template v-slot:prepend>
              <q-icon name="check_circle" />
            </template>
            <template v-slot:append>
              <q-btn
                :icon="showConfirmPassword ? 'visibility_off' : 'visibility'"
                flat
                round
                dense
                @click="showConfirmPassword = !showConfirmPassword"
              />
            </template>
          </q-input>

          <!-- Info Banner -->
          <q-banner class="bg-info text-white" rounded dense>
            <template v-slot:avatar>
              <q-icon name="info" />
            </template>
            <div class="text-caption">
              Make sure to remember your new password. You'll need it to log in next time.
            </div>
          </q-banner>
        </q-form>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Cancel" color="grey" v-close-popup :disable="loading" />
        <q-btn
          label="Change Password"
          color="primary"
          icon="save"
          @click="handleSubmit"
          :loading="loading"
          :disable="!isFormValid"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { usersAPI } from 'src/services/api'

const $q = useQuasar()

// Props & Emits
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

// State
const loading = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

// Password validation
const validatePasswordPolicy = (password) => {
  if (!password) return true // Let required rule handle empty

  if (password.length < 8) {
    return 'Password must be at least 8 characters'
  }
  if (!/[A-Z]/.test(password)) {
    return 'Password must contain at least one uppercase letter'
  }
  if (!/[a-z]/.test(password)) {
    return 'Password must contain at least one lowercase letter'
  }
  if (!/[0-9]/.test(password)) {
    return 'Password must contain at least one digit'
  }
  if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
    return 'Password must contain at least one special character'
  }
  return true
}

// Form validation
const isFormValid = computed(() => {
  return currentPassword.value &&
         newPassword.value &&
         confirmPassword.value &&
         newPassword.value === confirmPassword.value &&
         validatePasswordPolicy(newPassword.value) === true
})

// Password strength calculator
const passwordStrength = computed(() => {
  const pwd = newPassword.value
  if (!pwd) return { value: 0, color: 'grey', label: '' }

  let strength = 0
  if (pwd.length >= 8) strength += 0.2
  if (pwd.length >= 12) strength += 0.1
  if (/[a-z]/.test(pwd)) strength += 0.15
  if (/[A-Z]/.test(pwd)) strength += 0.15
  if (/[0-9]/.test(pwd)) strength += 0.15
  if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(pwd)) strength += 0.15
  if (pwd.length >= 16) strength += 0.1

  if (strength < 0.4) return { value: strength, color: 'negative', label: 'Weak' }
  if (strength < 0.7) return { value: strength, color: 'warning', label: 'Medium' }
  return { value: strength, color: 'positive', label: 'Strong' }
})

// Methods
const generatePassword = () => {
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const lowercase = 'abcdefghijklmnopqrstuvwxyz'
  const digits = '0123456789'
  const special = '!@#$%^&*()_+-=[]{}|;:,.<>?'
  const all = uppercase + lowercase + digits + special

  // Ensure at least one of each required type
  let password = ''
  password += uppercase[Math.floor(Math.random() * uppercase.length)]
  password += lowercase[Math.floor(Math.random() * lowercase.length)]
  password += digits[Math.floor(Math.random() * digits.length)]
  password += special[Math.floor(Math.random() * special.length)]

  // Fill the rest randomly
  for (let i = password.length; i < 12; i++) {
    password += all[Math.floor(Math.random() * all.length)]
  }

  // Shuffle the password
  newPassword.value = password.split('').sort(() => Math.random() - 0.5).join('')
  confirmPassword.value = newPassword.value
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    $q.notify({
      type: 'warning',
      message: 'Please fill in all required fields correctly',
      position: 'top'
    })
    return
  }

  loading.value = true
  try {
    await usersAPI.changeOwnPassword(currentPassword.value, newPassword.value)

    $q.notify({
      type: 'positive',
      message: 'Password changed successfully',
      position: 'top'
    })

    emit('update:modelValue', false)
    emit('success')

    // Reset form
    setTimeout(() => {
      currentPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
      showCurrentPassword.value = false
      showNewPassword.value = false
      showConfirmPassword.value = false
    }, 300)
  } catch (error) {
    console.error('Failed to change password:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to change password',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}
</script>
