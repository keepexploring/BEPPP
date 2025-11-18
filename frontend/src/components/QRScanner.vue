<template>
  <div class="qr-scanner">
    <div v-if="!scanning" class="text-center">
      <q-btn
        :label="buttonLabel"
        :icon="buttonIcon"
        color="primary"
        @click="startScanning"
        :loading="loading"
      />
    </div>

    <div v-else>
      <div class="scanner-container">
        <div id="qr-reader" style="width: 100%"></div>

        <div class="scanner-actions q-mt-md">
          <q-btn
            label="Cancel"
            flat
            color="negative"
            @click="stopScanning"
          />
        </div>
      </div>
    </div>

    <!-- Manual entry fallback -->
    <div v-if="showManualEntry" class="q-mt-md">
      <q-input
        v-model="manualInput"
        :label="manualLabel"
        outlined
        @keyup.enter="handleManualEntry"
      >
        <template v-slot:append>
          <q-btn
            flat
            dense
            icon="check"
            color="primary"
            @click="handleManualEntry"
          />
        </template>
      </q-input>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { Html5Qrcode } from 'html5-qrcode'
import { useQuasar } from 'quasar'

const props = defineProps({
  buttonLabel: {
    type: String,
    default: 'Scan QR Code'
  },
  buttonIcon: {
    type: String,
    default: 'qr_code_scanner'
  },
  manualLabel: {
    type: String,
    default: 'Or enter User ID manually'
  },
  showManualEntry: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['scanned', 'error'])

const $q = useQuasar()

const scanning = ref(false)
const loading = ref(false)
const manualInput = ref('')
let html5QrCode = null

const startScanning = async () => {
  loading.value = true

  try {
    html5QrCode = new Html5Qrcode('qr-reader')

    const config = {
      fps: 10,
      qrbox: { width: 250, height: 250 }
    }

    await html5QrCode.start(
      { facingMode: 'environment' }, // Use back camera on mobile
      config,
      onScanSuccess,
      onScanError
    )

    scanning.value = true
  } catch (error) {
    console.error('Error starting QR scanner:', error)
    $q.notify({
      type: 'negative',
      message: 'Unable to access camera. Please check permissions.',
      position: 'top'
    })
    emit('error', error)
  } finally {
    loading.value = false
  }
}

const stopScanning = async () => {
  if (html5QrCode) {
    try {
      await html5QrCode.stop()
      scanning.value = false
    } catch (error) {
      console.error('Error stopping scanner:', error)
    }
  }
}

const onScanSuccess = (decodedText, decodedResult) => {
  console.log('QR Code scanned:', decodedText)

  $q.notify({
    type: 'positive',
    message: 'QR Code scanned successfully!',
    position: 'top',
    timeout: 1000
  })

  emit('scanned', decodedText)
  stopScanning()
}

const onScanError = (errorMessage) => {
  // Don't log every scan error, they're too frequent
  // console.log('Scan error:', errorMessage)
}

const handleManualEntry = () => {
  if (manualInput.value.trim()) {
    emit('scanned', manualInput.value.trim())
    manualInput.value = ''
  }
}

onBeforeUnmount(() => {
  stopScanning()
})
</script>

<style scoped>
.qr-scanner {
  width: 100%;
}

.scanner-container {
  position: relative;
}

.scanner-actions {
  display: flex;
  justify-content: center;
}

/* Style the QR scanner */
:deep(#qr-reader) {
  border: 2px solid #1976D2;
  border-radius: 8px;
  overflow: hidden;
}

:deep(#qr-reader video) {
  border-radius: 8px;
}
</style>
