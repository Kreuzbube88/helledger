<script setup>
import { ref, computed, watch, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Toaster } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import OnboardingWizard from '@/components/OnboardingWizard.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const { locale } = useI18n()

const showNav = computed(() => !!route.meta?.requiresAuth && auth.isAuthenticated)

// Sync i18n locale to user's stored language on login / user change
watch(() => auth.user?.language, (lang) => {
  if (lang && lang !== locale.value) {
    locale.value = lang
    localStorage.setItem('helledger-lang', lang)
  }
}, { immediate: true })

const wizardActive = ref(false)
watchEffect(() => {
  if (showNav.value && auth.user && !auth.user.active_household_id) {
    wizardActive.value = true
  }
})
const showWizard = computed(() => showNav.value && wizardActive.value)
function onWizardDone() { wizardActive.value = false; auth.fetchUser() }
</script>

<template>
  <!-- Ambient layers — visible only in dark mode via CSS -->
  <div aria-hidden="true">
    <div class="ambient-orb ambient-orb-1" />
    <div class="ambient-orb ambient-orb-2" />
    <div class="ambient-orb ambient-orb-3" />
    <div class="ambient-orb ambient-orb-4" />
    <div class="aurora-sweep" />
  </div>

  <AppNav v-if="showNav" />
  <div
    class="min-h-dvh transition-all duration-300"
    :class="showNav ? 'md:pl-64 pb-20 md:pb-0' : ''"
  >
    <RouterView />
  </div>
  <OnboardingWizard v-if="showWizard" @done="onWizardDone" />
  <ConfirmDialog />
  <Toaster rich-colors position="top-right" />
</template>
