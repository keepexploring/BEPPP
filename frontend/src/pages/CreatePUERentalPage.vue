<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" @click="$router.back()" class="q-mr-md" />
      <div class="text-h4 col">Create PUE Rental</div>
    </div>

    <PUERentalForm
      @success="onSuccess"
      @cancel="onCancel"
    >
      <template #title>
        Rental Information
      </template>
    </PUERentalForm>
  </q-page>
</template>

<script setup>
import { useRouter } from 'vue-router'
import PUERentalForm from 'src/components/PUERentalForm.vue'

const router = useRouter()

const onSuccess = (rental) => {
  // Navigate to rental detail or back to dashboard
  router.push({ name: 'pue-rental-detail', params: { id: rental.pue_rental_id } })
}

const onCancel = () => {
  router.back()
}
</script>
