import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'helledger_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY))
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setToken(newToken) {
    token.value = newToken
    newToken
      ? localStorage.setItem(TOKEN_KEY, newToken)
      : localStorage.removeItem(TOKEN_KEY)
  }

  async function login(email, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw err
    }
    const { access_token } = await res.json()
    setToken(access_token)
    await fetchUser()
  }

  async function register(name, email, password) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, email, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw err
    }
    const { access_token } = await res.json()
    setToken(access_token)
    await fetchUser()
  }

  async function fetchUser() {
    const t = localStorage.getItem(TOKEN_KEY)
    if (!t) return
    const res = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${t}` },
      credentials: 'include',
    })
    if (res.ok) user.value = await res.json()
    else setToken(null)
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  return { token, user, isAuthenticated, isAdmin, setToken, login, register, fetchUser, logout }
})
