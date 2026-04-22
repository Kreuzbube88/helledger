<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Toaster } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import OnboardingWizard from '@/components/OnboardingWizard.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const showNav = computed(() => !!route.meta?.requiresAuth && auth.isAuthenticated)

// Show wizard when authenticated user has no household yet
const wizardActive = ref(false)
watch(
  () => auth.user,
  (user) => {
    if (user && !user.active_household_id) wizardActive.value = true
  },
  { immediate: true },
)

const showWizard = computed(() => showNav.value && wizardActive.value)

function onWizardDone() {
  wizardActive.value = false
  auth.fetchUser()
}
</script>

<template>
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
