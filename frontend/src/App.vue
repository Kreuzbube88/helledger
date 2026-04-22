<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Toaster } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const showNav = computed(() => !!route.meta?.requiresAuth && auth.isAuthenticated)
</script>

<template>
  <AppNav v-if="showNav" />
  <div
    class="min-h-dvh transition-all duration-300"
    :class="showNav ? 'md:pl-64 pb-20 md:pb-0' : ''"
  >
    <RouterView />
  </div>
  <Toaster rich-colors position="top-right" />
</template>
