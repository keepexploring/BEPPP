<template>
  <div class="fullscreen bg-gradient flex flex-center">
    <div class="text-center">
      <div style="font-size: 120px">404</div>
      <div class="text-h5 q-mt-md">Oops! Page not found.</div>
      <div class="text-subtitle1 text-grey-7 q-mt-sm">
        The page you're looking for doesn't exist.
      </div>
      <q-btn
        label="Go Home"
        color="primary"
        size="lg"
        class="q-mt-lg"
        :to="{ name: 'dashboard' }"
      />
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.bg-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}
</style>
