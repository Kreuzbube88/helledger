<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Toaster } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import OnboardingWizard from '@/components/OnboardingWizard.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const showNav = computed(() => !!route.meta?.requiresAuth && auth.isAuthenticated)
const showWizard = computed(() => showNav.value && !!auth.user && !auth.user.active_household_id)
function onWizardDone() { auth.fetchUser() }
</script>

<template>
  <!-- Ambient layers — visible only in dark mode via CSS -->
  <div aria-hidden="true">
    <div class="ambient-orb ambient-orb-1" />
    <div class="ambient-orb ambient-orb-2" />
    <div class="ambient-orb ambient-orb-3" />
    <div class="ambient-orb ambient-orb-4" />
    <div class="aurora-sweep" />
    <div class="scan-line" />
  </div>

  <AppNav v-if="showNav" />
  <div
    class="min-h-dvh transition-all duration-300"
    :class="showNav ? 'md:pl-64 pb-20 md:pb-0' : ''"
  >
    <RouterView />
  </div>
  <OnboardingWizard v-if="showWizard" @done="onWizardDone" />
  <Toaster rich-colors position="top-right" />
</template>
