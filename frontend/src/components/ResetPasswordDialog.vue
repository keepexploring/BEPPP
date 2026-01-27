<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" persistent>
    <q-card style="min-width: 550px">
      <!-- Confirmation Step -->
      <template v-if="!resetComplete">
        <q-card-section class="row items-center q-pb-none">
          <q-icon name="lock_reset" color="orange" size="32px" class="q-mr-md" />
          <div class="text-h6">Reset Password</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <q-banner class="bg-orange-1 text-orange-9" rounded>
            <template v-slot:avatar>
              <q-icon name="warning" color="orange" />
            </template>
            <div class="text-body2">
              <strong>Warning:</strong> This will immediately change the user's password. They will need to be notified of the new password.
            </div>
          </q-banner>

          <div class="q-mt-md q-mb-md">
            <div class="text-body2 q-mb-xs"><strong>User:</strong> {{ displayName }}</div>
            <div class="text-body2 q-mb-xs"><strong>Username:</strong> {{ user?.username }}</div>
          </div>

          <!-- Password Generation Options -->
          <div class="q-mb-md">
            <div class="text-subtitle2 q-mb-sm">Password Options:</div>
            <q-option-group
              v-model="passwordMode"
              :options="passwordModeOptions"
              color="primary"
              inline
            />
          </div>

          <!-- Custom Password Input -->
          <div v-if="passwordMode === 'custom'" class="q-mb-md">
            <q-input
              v-model="customPassword"
              :type="showPassword ? 'text' : 'password'"
              label="New Password *"
              outlined
              :rules="[val => !!val || 'Password is required', validatePasswordPolicy]"
              hint="Min 8 chars, uppercase, lowercase, digit, special char"
            >
              <template v-slot:prepend>
                <q-icon name="lock" />
              </template>
              <template v-slot:append>
                <q-btn
                  :icon="showPassword ? 'visibility_off' : 'visibility'"
                  flat
                  round
                  dense
                  @click="showPassword = !showPassword"
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
            <div v-if="customPassword" class="q-mt-sm">
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
          </div>

          <div v-else class="text-caption text-grey-7">
            A random 12-character secure password will be generated automatically.
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey" v-close-popup :disable="loading" />
          <q-btn
            label="Reset Password"
            color="orange"
            icon="lock_reset"
            @click="handleReset"
            :loading="loading"
            :disable="passwordMode === 'custom' && !isCustomPasswordValid"
          />
        </q-card-actions>
      </template>

      <!-- Success Step -->
      <template v-else>
        <q-card-section class="row items-center q-pb-none">
          <q-icon name="check_circle" color="positive" size="32px" class="q-mr-md" />
          <div class="text-h6">Password Reset Successful</div>
          <q-space />
          <q-btn icon="close" flat round dense @click="handleClose" />
        </q-card-section>

        <q-card-section>
          <q-banner class="bg-red-1 text-red-9" rounded>
            <template v-slot:avatar>
              <q-icon name="info" color="red" />
            </template>
            <div class="text-body2">
              <strong>Important:</strong> Make sure to copy and save this password. It cannot be retrieved later.
            </div>
          </q-banner>

          <div class="q-mt-md">
            <div class="text-subtitle2 q-mb-sm">New Password for {{ displayName }}:</div>
            <q-input
              :model-value="newPassword"
              outlined
              readonly
              bg-color="blue-1"
              class="text-h6"
            >
              <template v-slot:append>
                <q-btn
                  :icon="copied ? 'check' : 'content_copy'"
                  :color="copied ? 'positive' : 'primary'"
                  flat
                  round
                  dense
                  @click="copyToClipboard"
                >
                  <q-tooltip>{{ copied ? 'Copied!' : 'Copy to clipboard' }}</q-tooltip>
                </q-btn>
              </template>
            </q-input>
            <div class="text-caption text-grey-7 q-mt-xs">
              Please share this password securely with {{ user?.first_names || user?.Name || 'the user' }}.
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            label="Done"
            color="primary"
            @click="handleClose"
          />
        </q-card-actions>
      </template>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuasar, copyToClipboard as qCopyToClipboard } from 'quasar'
import { usersAPI } from 'src/services/api'

const $q = useQuasar()

// Props & Emits
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

// State
const loading = ref(false)
const resetComplete = ref(false)
const newPassword = ref('')
const copied = ref(false)
const passwordMode = ref('auto')
const customPassword = ref('')
const showPassword = ref(false)

// Password mode options
const passwordModeOptions = [
  { label: 'Auto-generate', value: 'auto' },
  { label: 'Choose password', value: 'custom' }
]

// Computed
const displayName = computed(() => {
  if (props.user?.first_names && props.user?.last_name) {
    return `${props.user.first_names} ${props.user.last_name}`
  }
  return props.user?.Name || props.user?.username || 'Unknown User'
})

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

const isCustomPasswordValid = computed(() => {
  if (passwordMode.value !== 'custom') return true
  return customPassword.value && validatePasswordPolicy(customPassword.value) === true
})

// Password strength calculator
const passwordStrength = computed(() => {
  const pwd = customPassword.value
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
  customPassword.value = password.split('').sort(() => Math.random() - 0.5).join('')
}

const handleReset = async () => {
  if (!props.user?.user_id) {
    $q.notify({
      type: 'negative',
      message: 'User ID not found',
      position: 'top'
    })
    return
  }

  loading.value = true
  try {
    const passwordToSend = passwordMode.value === 'custom' ? customPassword.value : null
    const response = await usersAPI.resetPassword(props.user.user_id, passwordToSend)
    newPassword.value = response.data.new_password
    resetComplete.value = true

    $q.notify({
      type: 'positive',
      message: 'Password reset successfully',
      position: 'top'
    })
  } catch (error) {
    console.error('Failed to reset password:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Failed to reset password',
      position: 'top'
    })
  } finally {
    loading.value = false
  }
}

const copyToClipboard = async () => {
  try {
    await qCopyToClipboard(newPassword.value)
    copied.value = true

    $q.notify({
      type: 'positive',
      message: 'Password copied to clipboard',
      position: 'top',
      timeout: 1000
    })

    // Reset copied state after 3 seconds
    setTimeout(() => {
      copied.value = false
    }, 3000)
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to copy password',
      position: 'top'
    })
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
  emit('success')

  // Reset state after dialog closes
  setTimeout(() => {
    resetComplete.value = false
    newPassword.value = ''
    copied.value = false
    passwordMode.value = 'auto'
    customPassword.value = ''
    showPassword.value = false
  }, 300)
}
</script>
