<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

onMounted(async () => {
  const token = route.query.access_token
  if (token) {
    auth.setToken(token)
    await auth.fetchUser()
    router.replace('/dashboard')
  } else {
    router.replace('/login')
  }
})
</script>

<template>
  <div class="flex h-screen items-center justify-center">
    <p class="text-muted-foreground">{{ $t('auth.redirecting') }}</p>
  </div>
</template>
