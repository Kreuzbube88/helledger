import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const stored = localStorage.getItem('helledger-theme')
  const isDark = ref(
    stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
  )

  function toggle() {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem('helledger-theme', isDark.value ? 'dark' : 'light')
  }

  function init() {
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  return { isDark, toggle, init }
})
