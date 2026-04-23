import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import de from './locales/de.json'
import en from './locales/en.json'

import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'
import './assets/main.css'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('helledger-lang') || 'de',
  fallbackLocale: 'en',
  messages: { de, en },
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(i18n)

const themeStore = useThemeStore()
themeStore.init()

app.mount('#app')

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {})
  })
}
