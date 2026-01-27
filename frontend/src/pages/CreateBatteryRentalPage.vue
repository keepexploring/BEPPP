<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" @click="$router.back()" class="q-mr-md" />
      <div class="text-h4 col">Create Battery Rental</div>
    </div>

    <BatteryRentalForm
      @success="onSuccess"
      @cancel="onCancel"
    >
      <template #title>
        Rental Information
      </template>
    </BatteryRentalForm>
  </q-page>
</template>

<script setup>
import { useRouter } from 'vue-router'
import BatteryRentalForm from 'src/components/BatteryRentalForm.vue'

const router = useRouter()

const onSuccess = (rental) => {
  // Navigate to rental detail or back to dashboard
  router.push({ name: 'battery-rental-detail', params: { id: rental.rental_id } })
}

const onCancel = () => {
  router.back()
}
</script>
